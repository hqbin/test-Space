"""
数据库管理 API

提供以下功能：
- 表结构查询、数据增删改查
- SQL 执行
- 数据库备份：导出完整 SQL（DDL + DML）
- 数据库恢复：异步追加式恢复（不清库，已存在记录跳过）

备份格式说明：
- 使用 SQLAlchemy 反射表结构，用 CreateTable DDL 生成 CREATE TABLE IF NOT EXISTS 语句
- INSERT 语句恢复时会自动加 ON CONFLICT DO NOTHING 保证幂等
- 文件编码 UTF-8
- 流式输出，支持 GB 级数据量

恢复策略（只支持追加模式）：
- 对现有数据绝对无损：已存在的表跳过（CREATE TABLE IF NOT EXISTS），已存在的行跳过（ON CONFLICT DO NOTHING）
- 仅补充缺失记录：如果数据库里少某条数据，才会插入
- 所有 DB 操作用 AUTOCOMMIT 独立提交，避免事务级联失败
- 用 exec_driver_sql 绕过 SQLAlchemy 的 :name 参数解析
- 外键失败的 INSERT 会多轮重试，正确处理自引用外键和跨表依赖顺序
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import logging
import re
import threading
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, and_, cast, delete, inspect, or_, select, text, update, String, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from auth import get_current_user, has_permission, is_super_admin
from database import engine, get_db
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["数据库管理"])


# ============================================================================
# 权限 & 工具
# ============================================================================

def _ensure_database_permission(current_user: User, db: Session):
    if is_super_admin(current_user):
        return
    if not has_permission(current_user, db, "database"):
        raise HTTPException(status_code=403, detail="没有数据库管理权限")


def _get_table_or_404(table_name: str) -> Table:
    metadata = MetaData()
    try:
        return Table(table_name, metadata, autoload_with=engine)
    except Exception:
        raise HTTPException(status_code=404, detail=f"数据表不存在: {table_name}")


def _friendly_db_error(action: str, error: Exception) -> str:
    msg = str(error).lower()
    if "foreign key" in msg or "constraint" in msg:
        return f"{action}失败：存在关联数据约束，请先处理关联记录"
    if "unique" in msg or "duplicate" in msg:
        return f"{action}失败：存在唯一性冲突（重复数据）"
    return f"{action}失败: {str(error)}"


def _safe_cell_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"<BLOB {len(value)} bytes>"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (dict, list, tuple, set)):
        s = str(value)
        return s if len(s) <= 2000 else s[:2000] + "...(truncated)"
    if isinstance(value, str):
        return value if len(value) <= 5000 else value[:5000] + "...(truncated)"
    return value


def _safe_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _safe_cell_value(v) for k, v in row.items()}


# ============================================================================
# Pydantic 请求体
# ============================================================================

class RowPayload(BaseModel):
    data: Dict[str, Any]


class UpdateRowPayload(BaseModel):
    pk: Dict[str, Any]
    data: Dict[str, Any]


class DeleteRowPayload(BaseModel):
    pk: Dict[str, Any]


class SqlPayload(BaseModel):
    sql: str


class BackupPayload(BaseModel):
    tables: Optional[List[str]] = None


# ============================================================================
# 备份：生成 SQL
# ============================================================================

# 备份接口并发限制：同一时刻最多 2 个备份任务（数据量大时避免连接爆满）
_backup_semaphore = threading.Semaphore(2)


def _escape_sql_literal(value: Any) -> str:
    """转义 SQL 字面量。PostgreSQL 标准双单引号转义。"""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return f"'{value.isoformat()}'"
    if isinstance(value, Decimal):
        return f"'{str(value)}'"
    if isinstance(value, bytes):
        return f"'\\x{value.hex()}'"
    s = str(value)
    s = s.replace("\\", "\\\\").replace("'", "''")
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f"E'{s}'"


@router.post("/backup")
def backup_database(
    payload: Optional[BackupPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """流式导出完整数据库备份到 SQL 文件

    - 使用 SQLAlchemy CreateTable 生成 DDL（包含类型、默认值、FK、约束）
    - 自动加 CREATE TABLE IF NOT EXISTS 保证幂等
    - 流式输出：按表、按行分批生成 SQL，直接写到 HTTP 响应，
      不会把整个 SQL 文件加载到内存，支持 GB 级数据量
    - 恢复时会自动加 ON CONFLICT DO NOTHING
    - 并发限制：同时最多 2 个备份任务，防止连接池被占满影响正常用户
    """
    _ensure_database_permission(current_user, db)

    # 并发保护：超过并发限制立即返回 429，让客户端稍后重试
    acquired = _backup_semaphore.acquire(blocking=False)
    if not acquired:
        raise HTTPException(
            status_code=429,
            detail="服务器正在处理其他备份请求，请稍后再试"
        )

    # 反射阶段如果失败必须释放信号量
    try:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        if payload and payload.tables:
            tables = [t for t in payload.tables if t in all_tables]
            if not tables:
                raise HTTPException(status_code=400, detail="没有有效的表名")
        else:
            tables = all_tables

        # 反射所有表
        reflection_metadata = MetaData()
        reflected: Dict[str, Table] = {}
        for table_name in tables:
            try:
                reflected[table_name] = Table(table_name, reflection_metadata, autoload_with=engine)
            except Exception as e:
                logger.warning(f"备份：反射表 {table_name} 失败: {e}")

        # 按依赖顺序排序（父表在前）
        try:
            ordered_tables = [t for t in reflection_metadata.sorted_tables if t.name in reflected]
        except Exception:
            ordered_tables = list(reflected.values())

        # 预先生成所有 DDL 语句（表数量通常 < 100，不会有内存压力）
        ddl_list: List[tuple] = []
        for tbl in ordered_tables:
            try:
                ddl = str(CreateTable(tbl).compile(engine)).strip()
                ddl = re.sub(r'^CREATE\s+TABLE\s+', 'CREATE TABLE IF NOT EXISTS ', ddl, count=1, flags=re.IGNORECASE)
                ddl_list.append((tbl.name, ddl.rstrip(';') + ";"))
            except Exception as e:
                logger.warning(f"备份：生成 {tbl.name} DDL 失败: {e}")
                ddl_list.append((tbl.name, f"-- WARNING: 生成 {tbl.name} 的 DDL 失败: {e}"))
    except Exception:
        _backup_semaphore.release()
        raise

    def _stream_backup():
        """Generator：分批生成 SQL 字节流。结束或异常时释放信号量"""
        try:
            # 头部
            header = (
                "-- ============================================================\n"
                "-- 测试用例管理平台 - 数据库备份\n"
                f"-- 备份时间: {datetime.now().isoformat()}\n"
                f"-- 表数量:   {len(ordered_tables)}\n"
                "-- ============================================================\n\n"
            )
            yield header.encode("utf-8")

            # DDL 部分
            yield b"-- -------------------- Table Structure --------------------\n\n"
            for tbl_name, ddl in ddl_list:
                yield (ddl + "\n\n").encode("utf-8")

            # DML 部分：按表、按行流式查询
            yield b"-- -------------------- Table Data --------------------\n\n"

            # 用单独的连接流式查询，避免长事务占用主连接池
            with engine.connect().execution_options(stream_results=True, max_row_buffer=1000) as conn:
                for tbl in ordered_tables:
                    columns = [c.name for c in tbl.columns]
                    cols_str = ", ".join(f'"{c}"' for c in columns)

                    # 先查一下总行数（用于注释）
                    try:
                        total = conn.execute(select(func.count()).select_from(tbl)).scalar() or 0
                    except Exception:
                        total = 0

                    if total == 0:
                        continue

                    yield f"-- 数据表: {tbl.name}（{total} 行）\n".encode("utf-8")

                    # 流式游标读取所有行
                    try:
                        result = conn.execute(select(tbl))
                        batch = []
                        batch_size = 500
                        for row in result:
                            row_dict = dict(row._mapping)
                            values = [_escape_sql_literal(row_dict.get(c)) for c in columns]
                            batch.append(f'INSERT INTO "{tbl.name}" ({cols_str}) VALUES ({", ".join(values)});')
                            if len(batch) >= batch_size:
                                yield ("\n".join(batch) + "\n").encode("utf-8")
                                batch.clear()
                        if batch:
                            yield ("\n".join(batch) + "\n").encode("utf-8")
                        yield b"\n"
                    except Exception as e:
                        logger.warning(f"备份：导出 {tbl.name} 数据失败: {e}")
                        yield f"-- WARNING: 备份 {tbl.name} 数据失败: {e}\n\n".encode("utf-8")
        finally:
            # 无论成功、异常、客户端断开，都释放信号量
            _backup_semaphore.release()
            logger.info(f"备份任务结束（用户: {current_user.username}），已释放并发槽位")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"

    return StreamingResponse(
        _stream_backup(),
        media_type="application/sql",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# 恢复：任务管理
# ============================================================================

# 内存任务表。用锁保护并发写入。
restore_tasks: Dict[str, Dict] = {}
_tasks_lock = threading.Lock()
_MAX_KEEP_TASKS = 10  # 最多保留多少个历史任务


def _put_task(task_id: str, task: Dict) -> None:
    """添加任务，并清理超出上限的旧任务（按状态优先保留 running，再按时间）"""
    with _tasks_lock:
        restore_tasks[task_id] = task
        if len(restore_tasks) > _MAX_KEEP_TASKS:
            sorted_items = sorted(
                restore_tasks.items(),
                key=lambda kv: (
                    0 if kv[1].get("status") == "running" else 1,
                    -(kv[1].get("created_at") or 0),
                ),
            )
            keep = dict(sorted_items[:_MAX_KEEP_TASKS])
            restore_tasks.clear()
            restore_tasks.update(keep)


def _get_task(task_id: str) -> Optional[Dict]:
    with _tasks_lock:
        return restore_tasks.get(task_id)


# ============================================================================
# 恢复：SQL 解析与规范化
# ============================================================================

def _split_sql_statements(sql_content: str, progress_cb=None) -> List[str]:
    """按分号拆分 SQL 语句，正确处理字符串转义（''）和括号嵌套，跳过行注释

    大文件（> 10MB）建议传 progress_cb，签名为 callback(percent: int)，
    会在解析到文件不同位置时回调，让调用方能更新进度
    """
    statements = []
    current_stmt = []
    in_string = False
    paren_depth = 0
    line_comment = False

    i = 0
    n = len(sql_content)
    next_cb_at = max(n // 20, 1024 * 1024) if progress_cb else -1
    while i < n:
        char = sql_content[i]

        if char == '-' and i + 1 < n and sql_content[i + 1] == '-' and not in_string:
            line_comment = True
        elif char == '\n':
            line_comment = False

        if line_comment:
            i += 1
            continue

        if char == "'" and not in_string:
            in_string = True
            current_stmt.append(char)
            i += 1
            continue
        if char == "'" and in_string:
            if i + 1 < n and sql_content[i + 1] == "'":
                current_stmt.append("''")
                i += 2
                continue
            in_string = False
            current_stmt.append(char)
            i += 1
            continue

        if not in_string:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
            elif char == ";" and paren_depth == 0:
                stmt = "".join(current_stmt).strip()
                if stmt and stmt.upper().lstrip().startswith(("INSERT", "CREATE", "ALTER", "DROP", "UPDATE", "DELETE")):
                    statements.append(stmt)
                current_stmt = []
                i += 1
                if progress_cb and i >= next_cb_at:
                    try:
                        progress_cb(int(i / n * 100))
                    except Exception:
                        pass
                    next_cb_at = i + max(n // 20, 1024 * 1024)
                continue

        current_stmt.append(char)
        i += 1

    if current_stmt:
        stmt = "".join(current_stmt).strip()
        if stmt and stmt.upper().lstrip().startswith(("INSERT", "CREATE", "ALTER", "DROP", "UPDATE", "DELETE")):
            statements.append(stmt)

    return statements


def _split_top_level_commas(body: str) -> List[str]:
    """按顶层逗号切分（忽略括号内和字符串内的逗号）"""
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    in_str = False
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "'" and not in_str:
            in_str = True
            current.append(ch)
        elif ch == "'" and in_str:
            if i + 1 < n and body[i + 1] == "'":
                current.append("''")
                i += 2
                continue
            in_str = False
            current.append(ch)
        elif not in_str:
            if ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)
        i += 1
    if current:
        tail = "".join(current).strip()
        if tail:
            parts.append(tail)
    return parts


def _fix_duplicate_primary_key(stmt: str) -> str:
    """防御：当 CREATE TABLE 同时有列级 PK 和表级 PK 时，移除列级 PK 避免 PostgreSQL 拒绝双主键"""
    if not stmt.upper().lstrip().startswith("CREATE TABLE"):
        return stmt

    start = stmt.find('(')
    end = stmt.rfind(')')
    if start < 0 or end < 0:
        return stmt

    body = stmt[start + 1:end]
    parts = _split_top_level_commas(body)

    has_table_level_pk = False
    for part in parts:
        p_upper = part.upper().lstrip()
        if re.match(r'^PRIMARY\s+KEY\s*\(', p_upper) or re.search(r'\bCONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\(', p_upper):
            has_table_level_pk = True
            break

    if not has_table_level_pk:
        return stmt

    new_parts = []
    for part in parts:
        p_upper = part.upper().lstrip()
        if (p_upper.startswith("CONSTRAINT ") or
                p_upper.startswith("PRIMARY KEY") or
                p_upper.startswith("FOREIGN KEY") or
                p_upper.startswith("UNIQUE") or
                p_upper.startswith("CHECK")):
            new_parts.append(part)
            continue
        fixed = re.sub(r'\s+PRIMARY\s+KEY\b', '', part, flags=re.IGNORECASE)
        new_parts.append(fixed)

    table_header_match = re.match(r'(\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[^\s(]+)\s*\(', stmt, re.IGNORECASE)
    if not table_header_match:
        return stmt
    header = table_header_match.group(1)
    tail = stmt[end + 1:]
    return f"{header} (\n    " + ",\n    ".join(new_parts) + f"\n){tail}"


# ============================================================================
# 恢复：后台任务
# ============================================================================

def _create_tables(logger_: logging.Logger, task_id: str, task: Dict,
                   create_stmts: List[str], errors: List[str]) -> None:
    """执行 CREATE TABLE 语句（IF NOT EXISTS 幂等），多轮重试解决外键依赖顺序"""
    if not create_stmts:
        return

    task["progress"] = 15
    task["message"] = "正在创建表..."

    create_list = []
    for stmt in create_stmts:
        fixed = _fix_duplicate_primary_key(stmt)
        fixed = re.sub(
            r'CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?',
            'CREATE TABLE IF NOT EXISTS ',
            fixed, count=1, flags=re.IGNORECASE,
        )
        create_list.append(fixed)

    # 多轮重试：遇到 "does not exist"（外键依赖的表未建）放到下一轮
    remaining = list(create_list)
    for _ in range(len(create_list) + 1):
        if not remaining:
            break
        failed_this_round: List[str] = []
        for stmt in remaining:
            try:
                with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                    conn.execute(text(stmt))
            except Exception as e:
                err_str = str(e).lower()
                is_dep_missing = (
                    "does not exist" in err_str or
                    ("relation" in err_str and "not exist" in err_str)
                )
                if is_dep_missing:
                    failed_this_round.append(stmt)
                else:
                    errors.append(f"创建表失败: {str(e)[:150]}")
                    logger_.error(f"[Restore {task_id}] 创建表失败: {e}; SQL: {stmt[:120]}")

        if len(failed_this_round) == len(remaining):
            for stmt in failed_this_round:
                errors.append(f"创建表失败（依赖无法解析）: {stmt[:80]}")
            break
        remaining = failed_this_round

    logger_.info(f"[Restore {task_id}] 创建表完成，剩余 {len(remaining)} 条未能创建")


def _build_upsert_clause(stmt: str) -> str:
    """将 INSERT INTO "table" (cols) VALUES (...) 转换为 upsert 语句。
    
    生成: INSERT INTO "table" (cols) VALUES (...) 
          ON CONFLICT (id) DO UPDATE SET col1=EXCLUDED.col1, col2=EXCLUDED.col2, ...
    
    策略：
    - 假设主键列名为 "id"（本项目所有表的主键都是 id）
    - 排除 id 列本身不参与 SET
    - 如果解析失败，回退到 ON CONFLICT DO NOTHING
    """
    try:
        # 格式: INSERT INTO "table_name" ("col1", "col2", ...) VALUES (...)
        # 先找到 INTO 关键字
        into_idx = stmt.upper().find("INTO")
        if into_idx < 0:
            return stmt + " ON CONFLICT DO NOTHING"
        after_into = stmt[into_idx + 4:]

        # 找到列名起始的 '('
        paren_start = after_into.find('(')
        if paren_start < 0:
            return stmt + " ON CONFLICT DO NOTHING"

        # 用括号深度匹配找到列名结束的 ')'
        depth = 0
        paren_end = -1
        for i, ch in enumerate(after_into[paren_start:]):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    paren_end = paren_start + i
                    break
        if paren_end < 0:
            return stmt + " ON CONFLICT DO NOTHING"

        # 提取列名字符串
        cols_str = after_into[paren_start + 1:paren_end]
        columns = [c.strip().strip('"').strip("'") for c in cols_str.split(',')]
        if not columns:
            return stmt + " ON CONFLICT DO NOTHING"

        # 验证列名闭括号之后存在 VALUES 关键字（避免列名误匹配）
        if "VALUES" not in after_into.upper()[paren_end + 1:]:
            return stmt + " ON CONFLICT DO NOTHING"

        # 确定主键列（默认 id）
        pk_col = "id"
        if pk_col not in columns:
            return stmt + " ON CONFLICT DO NOTHING"

        # 构建 SET 子句（排除主键列）
        set_parts = []
        for col in columns:
            if col.lower() != pk_col:
                set_parts.append(f'"{col}" = EXCLUDED."{col}"')

        if not set_parts:
            return stmt + " ON CONFLICT DO NOTHING"

        return f'{stmt} ON CONFLICT ("{pk_col}") DO UPDATE SET {", ".join(set_parts)}'
    except Exception:
        return stmt + " ON CONFLICT DO NOTHING"


def _extract_table_name(stmt: str) -> str:
    """从 INSERT INTO "table" (...) VALUES (...) 中提取表名"""
    upper = stmt.upper().lstrip()
    if not upper.startswith("INSERT INTO "):
        return ""
    after_into = stmt[stmt.upper().find("INTO") + 4:].lstrip()
    name = ""
    if after_into.startswith('"'):
        end = after_into.find('"', 1)
        if end > 0:
            name = after_into[1:end]
    else:
        space = after_into.find(' ')
        paren = after_into.find('(')
        end = space if space > 0 else paren
        if end > 0:
            name = after_into[:end].strip()
    return name


def _extract_id_from_insert(stmt: str) -> int:
    """从 INSERT INTO "t" (cols) VALUES (id, ...) 中提取 id 值"""
    upper = stmt.upper()
    vals_idx = upper.find("VALUES")
    if vals_idx < 0:
        return -1
    after_vals = stmt[vals_idx + 6:].lstrip().lstrip('(')
    # id 是 VALUES 中的第一个值
    first_val = after_vals.split(',')[0].strip()
    # 去掉可能的引号
    first_val = first_val.strip("'").strip('"')
    try:
        return int(first_val)
    except (ValueError, TypeError):
        return -1


def _get_dedup_key_columns(conn, table_name: str) -> List[str]:
    """获取 upsert 模式的业务键去重列。
    
    只对"关联表"（junction table）启用，判断条件：
    - 有至少 1 个 FK 列（引用其他表）
    - 除了 PK(id)、FK 列、时间戳列之外，最多 1 个其他数据列
    
    这可以避免对 users、test_plans 等普通表误触发 FK 去重。
    """
    try:
        # 查询 FK 列
        fk_result = conn.execute(text("""
            SELECT kcu.column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc
              ON kcu.constraint_name = tc.constraint_name
              AND kcu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = :tbl
              AND tc.table_schema = 'public'
              AND kcu.column_name != 'id'
        """), {"tbl": table_name})
        fk_cols = [row[0] for row in fk_result.fetchall()]
        if not fk_cols:
            return []

        # 查询所有列（判断是否为关联表）
        all_result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :tbl AND table_schema = 'public'
        """), {"tbl": table_name})
        fk_set = set(fk_cols)
        timestamp_cols = {'created_at', 'updated_at', 'deleted_at'}
        extra_cols = []
        for (col_name,) in all_result.fetchall():
            if col_name == 'id' or col_name in fk_set or col_name in timestamp_cols:
                continue
            extra_cols.append(col_name)

        # 额外数据列 ≤ 1 → 关联表，启用 FK 去重
        if len(extra_cols) <= 1:
            return fk_cols
        return []
    except Exception:
        return []


def _dedup_business_keys(conn, table_name: str, fk_columns: List[str],
                         restored_ids: set, logger_: logging.Logger,
                         task_id: str) -> None:
    """删除与已恢复行有相同 FK 值但 id 不同的旧行（upsert 模式专用）"""
    if not fk_columns or not restored_ids:
        return
    id_list = ",".join(str(i) for i in restored_ids)
    fk_join = " AND ".join(
        f't."{c}" = t2."{c}"' for c in fk_columns
    )
    sql = (
        f'DELETE FROM "{table_name}" t '
        f"WHERE t.id NOT IN ({id_list}) "
        f"AND EXISTS ("
        f"  SELECT 1 FROM \"{table_name}\" t2 "
        f"  WHERE t2.id IN ({id_list}) "
        f"  AND {fk_join}"
        f")"
    )
    try:
        result = conn.exec_driver_sql(sql)
        rc = result.rowcount if result.rowcount is not None else 0
        if rc > 0:
            logger_.info(
                f"[Restore {task_id}] [去重] {table_name}: "
                f"删除 {rc} 条 FK 键重复的旧行"
            )
    except Exception as e:
        logger_.warning(
            f"[Restore {task_id}] [去重] {table_name} 失败: {e}"
        )


def _insert_data(logger_: logging.Logger, task_id: str, task: Dict,
                 insert_stmts: List[str], errors: List[str],
                 mode: str = "append") -> Dict[str, int]:
    """执行 INSERT 语句。

    mode:
    - "append": ON CONFLICT DO NOTHING（默认，已存在的行跳过）
    - "upsert": ON CONFLICT DO UPDATE（覆盖模式，已存在的行用备份数据覆盖）

    关键点：
    - 恢复期间关闭外键约束（session_replication_role = replica），彻底解决插入顺序问题
    - 用 exec_driver_sql 绕过 SQLAlchemy 的 :name 参数解析
    - AUTOCOMMIT：每条独立提交，一条失败不影响其他
    - 完成后恢复外键约束

    返回统计: {inserted, skipped, failed, updated}
    """
    if not insert_stmts:
        return {"inserted": 0, "skipped": 0, "failed": 0, "updated": 0}

    task["progress"] = 30
    mode_label = "覆盖" if mode == "upsert" else "追加"
    task["message"] = f"正在{mode_label}数据 (0/{len(insert_stmts)})..."
    logger_.info(f"[Restore {task_id}] 开始{mode_label}数据, 共 {len(insert_stmts)} 条, mode={mode}")

    inserted_rows = 0
    updated_rows = 0
    skipped_conflict = 0
    final_errors: List[tuple] = []
    # upsert 模式：按表跟踪已恢复的 id，用于后续 FK 键去重
    table_restored_ids: Dict[str, set] = {}
    table_fk_cache: Dict[str, List[str]] = {}

    def _preprocess(stmt: str) -> str:
        s = stmt.rstrip(';').strip()
        # 检测 INSERT 语句末尾是否已有 ON CONFLICT（严格匹配关键词，避免字符串值误匹配）
        upper = s.upper()
        has_on_conflict = False
        idx = upper.find("ON CONFLICT")
        if idx >= 0:
            # 确保 "ON CONFLICT" 不在字符串字面量内
            in_str = False
            for i, ch in enumerate(s):
                if ch == "'":
                    in_str = not in_str
                if i == idx and not in_str:
                    has_on_conflict = True
                    break
        if not has_on_conflict:
            if mode == "upsert":
                s = _build_upsert_clause(s)
            else:
                s = s + " ON CONFLICT DO NOTHING"
        s = s.replace("%", "%%")
        return s

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # 关闭外键约束，彻底解决插入顺序问题
        try:
            conn.exec_driver_sql("SET session_replication_role = replica;")
            logger_.info(f"[Restore {task_id}] 已关闭外键约束检查")
        except Exception as e:
            logger_.warning(f"[Restore {task_id}] 关闭外键约束失败（继续执行）: {e}")

        try:
            batch_size = 200
            for batch_start in range(0, len(insert_stmts), batch_size):
                if task.get("cancel"):
                    task["message"] = "任务已被用户取消"
                    logger_.info(f"[Restore {task_id}] 收到取消请求，中断插入")
                    break

                batch_end = min(batch_start + batch_size, len(insert_stmts))
                for j in range(batch_start, batch_end):
                    raw = insert_stmts[j]
                    stmt = _preprocess(raw)
                    try:
                        result = conn.exec_driver_sql(stmt)
                        rc = result.rowcount if result.rowcount is not None else -1
                        if rc > 0:
                            if mode == "upsert" and rc >= 2:
                                updated_rows += 1
                            else:
                                inserted_rows += 1
                            if mode == "upsert":
                                tbl = _extract_table_name(raw)
                                rid = _extract_id_from_insert(raw)
                                if tbl and rid > 0:
                                    table_restored_ids.setdefault(tbl, set()).add(rid)
                        elif rc == 0:
                            skipped_conflict += 1
                        else:
                            inserted_rows += 1
                        if (j % 500 == 0) or rc <= 0:
                            logger_.debug(
                                f"[Restore {task_id}] SQL rowcount={rc}: "
                                f"{stmt[:120]}..."
                            )
                    except Exception as e:
                        final_errors.append((raw, str(e)))
                        logger_.error(
                            f"[Restore {task_id}] INSERT失败 rowcount=N/A: "
                            f"{stmt[:120]}... | {e}"
                        )

                # 当前批次结束后的去重（对已恢复完的表执行）
                if mode == "upsert" and batch_end == len(insert_stmts):
                    for tbl, ids in table_restored_ids.items():
                        if tbl not in table_fk_cache:
                            table_fk_cache[tbl] = _get_dedup_key_columns(conn, tbl)
                        fk_cols = table_fk_cache[tbl]
                        if fk_cols:
                            _dedup_business_keys(conn, tbl, fk_cols, ids,
                                                 logger_, task_id)

                task["executed"] = inserted_rows + updated_rows
                task["progress"] = 30 + int(batch_end / len(insert_stmts) * 60)
                task["message"] = (
                    f"正在插入：{batch_end}/{len(insert_stmts)}，"
                    f"已插入 {inserted_rows}，更新 {updated_rows}，"
                    f"跳过 {skipped_conflict}，失败 {len(final_errors)}"
                )
                if (batch_end % 5000 == 0) or (batch_end == len(insert_stmts)):
                    logger_.info(f"[Restore {task_id}] {task['message']}")

        finally:
            # 无论成功失败，都必须恢复外键约束
            try:
                conn.exec_driver_sql("SET session_replication_role = DEFAULT;")
                logger_.info(f"[Restore {task_id}] 已恢复外键约束检查")
            except Exception as e:
                logger_.error(f"[Restore {task_id}] 恢复外键约束失败: {e}")

    # 汇总错误信息到 errors 列表（最多 50 条样本）
    for stmt, err_str in final_errors[:50]:
        errors.append(f"INSERT 失败: {err_str[:120]}")
        logger_.error(f"[Restore {task_id}] INSERT 失败: {err_str[:200]}; SQL: {stmt[:120]}")

    failed_insert = len(final_errors)
    return {"inserted": inserted_rows, "skipped": skipped_conflict, "failed": failed_insert, "updated": updated_rows}


def _fix_serial_sequences(logger_: logging.Logger, task_id: str, task: Dict) -> None:
    """把每个 SERIAL 列的序列推到 MAX(id)，避免恢复后新增记录主键冲突"""
    task["message"] = "正在修复序列..."
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            seqs = conn.execute(text("""
                SELECT table_name, column_name,
                       pg_get_serial_sequence(quote_ident(table_name), column_name) AS seq
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_default LIKE 'nextval(%'
            """)).fetchall()
            for tbl, col, seq in seqs:
                if not seq:
                    continue
                try:
                    conn.execute(text(
                        f'SELECT setval(:seq, COALESCE((SELECT MAX("{col}") FROM "{tbl}"), 1), '
                        f'(SELECT MAX("{col}") FROM "{tbl}") IS NOT NULL)'
                    ), {"seq": seq})
                except Exception as e:
                    logger_.warning(f"[Restore {task_id}] 修复 {tbl}.{col} 序列失败: {e}")
            logger_.info(f"[Restore {task_id}] 序列修复完成，共处理 {len(seqs)} 个")
    except Exception as e:
        logger_.warning(f"[Restore {task_id}] 修复序列失败（忽略）: {e}")


def _run_restore_task(task_id: str, sql_content: str, mode: str = "append"):
    """后台执行恢复任务。由独立线程调用，不阻塞 FastAPI 事件循环。
    
    mode: "append"（追加，ON CONFLICT DO NOTHING）或 "upsert"（覆盖，ON CONFLICT DO UPDATE）
    """
    task = _get_task(task_id)
    if not task:
        return

    logger.info(f"[Restore {task_id}] 开始执行（追加模式）")

    try:
        # 解析 SQL 前更新进度：大文件解析可能耗时十几秒，前端需要感知任务已启动
        task["progress"] = 1
        task["message"] = f"正在解析 SQL 文件（{len(sql_content) / 1024 / 1024:.1f} MB）..."

        parse_start = time.time()

        # 把解析进度映射到 1-10% 这个区间
        def _parse_progress_cb(percent):
            task["progress"] = 1 + min(int(percent * 0.09), 9)
            task["message"] = (
                f"正在解析 SQL 文件（{len(sql_content) / 1024 / 1024:.1f} MB，"
                f"{percent}%）..."
            )

        statements = _split_sql_statements(sql_content, progress_cb=_parse_progress_cb)
        parse_elapsed = time.time() - parse_start
        logger.info(f"[Restore {task_id}] SQL 解析用时 {parse_elapsed:.1f}s, 共 {len(statements)} 条语句")

        create_stmts = [s for s in statements if s.upper().lstrip().startswith("CREATE TABLE")]
        insert_stmts = [s for s in statements if s.upper().lstrip().startswith("INSERT")]
        other_stmts = [s for s in statements if not s.upper().lstrip().startswith(("CREATE TABLE", "INSERT"))]

        task["total"] = len(statements)
        task["progress"] = 3
        task["message"] = (
            f"解析完成（用时 {parse_elapsed:.0f}s），"
            f"共 {len(statements)} 条语句（{len(create_stmts)} CREATE + {len(insert_stmts)} INSERT）"
        )
        logger.info(
            f"[Restore {task_id}] 解析完成: CREATE={len(create_stmts)}, "
            f"INSERT={len(insert_stmts)}, OTHER={len(other_stmts)}"
        )

        errors: List[str] = []

        # 1) 建表（IF NOT EXISTS 幂等，已存在的表跳过）
        _create_tables(logger, task_id, task, create_stmts, errors)

        # 2) 插数据
        stats = _insert_data(logger, task_id, task, insert_stmts, errors, mode=mode)

        # 3) 其他语句（ALTER/UPDATE/DELETE 等）
        if other_stmts:
            task["message"] = "正在执行其他语句..."
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                for stmt in other_stmts:
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        if len(errors) < 50:
                            errors.append(f"执行失败: {str(e)[:120]}")
                        logger.error(f"[Restore {task_id}] 其他语句失败: {e}; SQL: {stmt[:100]}")

        # 4) 修复序列（如果有插入数据）
        if stats["inserted"] > 0:
            _fix_serial_sequences(logger, task_id, task)

        # 5) 汇总
        if task.get("cancel"):
            task["status"] = "cancelled"
            task["progress"] = 100
            task["executed"] = stats["inserted"] + stats.get("updated", 0)
            task["errors"] = errors[:50]
            if mode == "upsert":
                task["message"] = (
                    f"已取消：已处理 {stats['inserted'] + stats.get('updated', 0)} 行，"
                    f"跳过 {stats['skipped']}，失败 {stats['failed']}"
                )
            else:
                task["message"] = (
                    f"已取消：已插入 {stats['inserted']} 行数据，"
                    f"跳过 {stats['skipped']}，失败 {stats['failed']}"
                )
            logger.info(f"[Restore {task_id}] {task['message']}")
            return

        task["status"] = "completed"
        task["progress"] = 100
        task["executed"] = stats["inserted"] + stats.get("updated", 0)
        task["errors"] = errors[:50]

        summary_parts = []
        if mode == "upsert":
            total_processed = stats["inserted"] + stats["updated"]
            summary_parts.append(f"成功处理 {total_processed} 行")
            if stats["inserted"] > 0:
                summary_parts.append(f"新增 {stats['inserted']} 行")
            if stats.get("updated", 0) > 0:
                summary_parts.append(f"覆盖更新 {stats['updated']} 条")
        else:
            summary_parts.append(f"成功插入 {stats['inserted']} 行数据")
        if stats["skipped"] > 0:
            summary_parts.append(f"跳过 {stats['skipped']} 条冲突")
        if stats["failed"] > 0:
            summary_parts.append(f"失败 {stats['failed']} 条")
        if errors:
            summary_parts.append(f"共 {len(errors)} 条错误")
        task["message"] = "恢复完成：" + "，".join(summary_parts)
        logger.info(f"[Restore {task_id}] {task['message']}")

    except Exception as e:
        import traceback
        logger.error(f"[Restore {task_id}] 任务异常: {e}\n{traceback.format_exc()}")
        task["status"] = "failed"
        task["message"] = f"恢复失败: {str(e)[:200]}"
        task["errors"] = [str(e)[:500]]
    finally:
        # 清理大字段，避免内存泄漏
        task.pop("sql_content", None)


# ============================================================================
# 恢复：HTTP 接口
# ============================================================================

@router.post("/restore/form")
async def restore_database_form(
    file: UploadFile = File(...),
    mode: str = Form("append"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传 SQL 文件，启动后台恢复任务，返回 task_id 供前端轮询进度。

    mode 参数：
    - "append"（默认）：追加模式，已存在的行跳过（ON CONFLICT DO NOTHING），绝对无损
    - "upsert"：覆盖模式，已存在的行用备份数据覆盖（ON CONFLICT DO UPDATE），
      适用于需要同步正式环境最新数据的场景
    """
    _ensure_database_permission(current_user, db)
    
    if mode not in ("append", "upsert"):
        raise HTTPException(status_code=400, detail="mode 必须是 append 或 upsert")

    if not file.filename or not file.filename.lower().endswith('.sql'):
        raise HTTPException(status_code=400, detail="只支持 .sql 文件")

    # 并发保护：同时只允许一个恢复任务运行
    with _tasks_lock:
        running = [tid for tid, t in restore_tasks.items() if t.get("status") == "running"]
        if running:
            raise HTTPException(
                status_code=409,
                detail=f"已有恢复任务正在进行中（task_id={running[0]}），请等待完成或取消后再试"
            )

    content = await file.read()
    try:
        sql_content = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            sql_content = content.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 或 GBK")

    task_id = uuid.uuid4().hex[:8]
    task = {
        "task_id": task_id,
        "status": "running",
        "progress": 0,
        "total": 0,
        "executed": 0,
        "errors": [],
        "message": "正在解析 SQL 文件...",
        "sql_content": sql_content,  # 跑完后会被 pop
        "created_at": datetime.now().timestamp(),
        "started_by": current_user.username,
        "mode": mode,
    }
    _put_task(task_id, task)
    mode_label = "覆盖恢复" if mode == "upsert" else "追加恢复"
    logger.info(f"[Restore {task_id}] 用户 {current_user.username} 启动{mode_label}任务")

    # 直接起 Thread 立刻运行，让前端首次轮询就能看到进度
    threading.Thread(
        target=_run_restore_task,
        args=(task_id, sql_content, mode),
        daemon=True,
    ).start()

    return {"code": 200, "data": {"task_id": task_id}, "message": f"{mode_label}任务已启动"}


@router.get("/restore/{task_id}")
def get_restore_progress(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """查询恢复任务进度。sql_content 大字段不返回给前端。"""
    task = _get_task(task_id)
    if not task:
        return {"code": 404, "message": "任务不存在"}
    info = {k: v for k, v in task.items() if k != "sql_content"}
    return {"code": 200, "data": info}


@router.post("/restore/{task_id}/cancel")
def cancel_restore_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消正在运行的恢复任务。

    设置 cancel 标志位。任务会在下一个 batch 边界（每 200 条 INSERT）检查并退出。
    已经插入的数据不会回滚（但因为是追加模式，已插入的只是补充数据，不会破坏现有数据）。
    """
    _ensure_database_permission(current_user, db)
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") != "running":
        return {"code": 200, "message": f"任务已 {task.get('status')}，无需取消"}
    task["cancel"] = True
    task["message"] = "正在取消任务..."
    logger.info(f"[Restore {task_id}] 收到用户取消请求")
    return {"code": 200, "message": "已发送取消信号，任务将在当前批次完成后停止"}


# ============================================================================
# 表管理 & SQL 执行
# ============================================================================

@router.get("/tables")
def get_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    inspector = inspect(engine)
    return {"code": 200, "data": {"tables": inspector.get_table_names()}}


@router.get("/tables/{table_name}/schema")
def get_table_schema(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail=f"数据表不存在: {table_name}")

    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name).get("constrained_columns") or []

    formatted_columns = []
    for col in columns:
        formatted_columns.append({
            "name": col.get("name"),
            "type": str(col.get("type")),
            "nullable": col.get("nullable", True),
            "default": str(col.get("default")) if col.get("default") is not None else None,
            "primary_key": col.get("name") in pk,
        })

    return {"code": 200, "data": {"table": table_name, "columns": formatted_columns, "primary_keys": pk}}


@router.get("/tables/{table_name}/rows")
def get_table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    table = _get_table_or_404(table_name)

    query = select(table)
    count_query = select(func.count()).select_from(table)
    if keyword:
        kw = keyword.strip()
        predicate = None

        # 快捷字段搜索: column:value 或 column=value
        pair_sep = ":" if ":" in kw else ("=" if "=" in kw else None)
        if pair_sep:
            field, value = kw.split(pair_sep, 1)
            field = field.strip()
            value = value.strip()
            if field in table.c and value != "":
                col = table.c[field]
                if value.isdigit():
                    predicate = (col == int(value))
                else:
                    predicate = cast(col, String).like(f"%{value}%")

        # 兜底：全字段模糊搜索
        if predicate is None:
            like_exp = f"%{kw}%"
            conditions = [cast(c, String).like(like_exp) for c in table.columns]
            if conditions:
                predicate = or_(*conditions)

        if predicate is not None:
            query = query.where(predicate)
            count_query = count_query.where(predicate)

    total = db.execute(count_query).scalar() or 0
    offset = (page - 1) * size
    paged = db.execute(query.offset(offset).limit(size)).mappings().all()
    safe_records = [_safe_row(dict(r)) for r in paged]
    return {"code": 200, "data": {"records": safe_records, "total": total, "page": page, "size": size}}


@router.post("/tables/{table_name}/rows")
def create_row(
    table_name: str,
    payload: RowPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    table = _get_table_or_404(table_name)
    try:
        db.execute(table.insert().values(**payload.data))
        db.commit()
        return {"code": 200, "message": "新增成功"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("新增", e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("新增", e))


@router.put("/tables/{table_name}/rows")
def update_row(
    table_name: str,
    payload: UpdateRowPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    table = _get_table_or_404(table_name)
    if not payload.pk:
        raise HTTPException(status_code=400, detail="缺少主键条件")

    where_clause = and_(*[table.c[k] == v for k, v in payload.pk.items() if k in table.c])
    try:
        result = db.execute(update(table).where(where_clause).values(**payload.data))
        db.commit()
        return {"code": 200, "message": "更新成功", "data": {"affected": result.rowcount}}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("更新", e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("更新", e))


@router.delete("/tables/{table_name}/rows")
def delete_row(
    table_name: str,
    payload: DeleteRowPayload,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    table = _get_table_or_404(table_name)
    if not payload.pk:
        raise HTTPException(status_code=400, detail="缺少主键条件")

    where_clause = and_(*[table.c[k] == v for k, v in payload.pk.items() if k in table.c])
    try:
        result = db.execute(delete(table).where(where_clause))
        db.commit()
        
        # 记录删除日志
        from utils.logger import log_operation, LogAction, LogModule
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.DATABASE,
            action=LogAction.DELETE,
            description=f"通过数据库管理删除记录：表={table_name}，条件={payload.pk}，影响行数={result.rowcount}",
            request=req
        )
        
        return {"code": 200, "message": "删除成功", "data": {"affected": result.rowcount}}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("删除", e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("删除", e))


@router.post("/sql")
def execute_sql(
    payload: SqlPayload,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_database_permission(current_user, db)
    sql = (payload.sql or "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL 不能为空")

    try:
        result = db.execute(text(sql))
        if result.returns_rows:
            rows = [_safe_row(dict(r)) for r in result.mappings().all()]
            
            # 记录SQL查询日志
            from utils.logger import log_operation, LogAction, LogModule
            log_operation(
                db=db,
                user_id=current_user.id,
                username=current_user.username,
                module=LogModule.DATABASE,
                action="sql_query",
                description=f"执行SQL查询：{sql[:200]}，返回 {len(rows)} 行",
                request=req
            )
            
            return {"code": 200, "data": {"type": "query", "rows": rows, "row_count": len(rows)}}
        db.commit()
        
        # 记录SQL变更日志
        from utils.logger import log_operation, LogAction, LogModule
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.DATABASE,
            action="sql_execute",
            description=f"执行SQL变更：{sql[:200]}，影响 {result.rowcount} 行",
            request=req
        )
        
        return {"code": 200, "data": {"type": "mutation", "affected": result.rowcount}}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("SQL执行", e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=_friendly_db_error("SQL执行", e))
