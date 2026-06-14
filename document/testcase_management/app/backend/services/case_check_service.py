"""
用例校对服务
V1.3 - 支持多Sheet处理
"""
import json
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

# 过滤 openpyxl 的样式警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from models import CaseTemplate
from utils.validation_rules import validate_field, fix_field, FieldIssue


@dataclass
class CheckTask:
    """校对任务"""
    task_id: str
    project_id: int
    template_id: int
    status: str  # processing, done, failed, needs_mapping
    progress: int
    original_file_name: str
    original_data: List[Dict]
    current_data: List[Dict]
    headers: List[str]
    field_mapping: Dict[str, str]
    template_fields: List[Dict]
    validation_results: List[Dict]
    statistics: Dict
    created_at: datetime
    expires_at: datetime
    error_message: Optional[str] = None
    # V1.3 新增字段
    sheet_name: str = ""
    header_row: int = 1


# 全局任务缓存
_check_tasks: Dict[str, CheckTask] = {}

# V1.3: 文件缓存（用于多Sheet选择后的校对）
_file_cache: Dict[str, Dict] = {}

# 任务过期时间（分钟）
TASK_EXPIRE_MINUTES = 30
FILE_CACHE_EXPIRE_MINUTES = 10


def cache_file(file_id: str, file_content: bytes, file_name: str) -> None:
    """
    缓存文件内容（V1.3新增）
    用于多Sheet选择后的校对
    """
    _file_cache[file_id] = {
        "content": file_content,
        "file_name": file_name,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=FILE_CACHE_EXPIRE_MINUTES)
    }


def get_cached_file(file_id: str) -> Optional[Dict]:
    """获取缓存的文件（V1.3新增）"""
    cached = _file_cache.get(file_id)
    if cached and datetime.now() > cached["expires_at"]:
        del _file_cache[file_id]
        return None
    return cached


def cleanup_file_cache() -> int:
    """清理过期的文件缓存（V1.3新增）"""
    now = datetime.now()
    expired = [fid for fid, data in _file_cache.items() if now > data["expires_at"]]
    for fid in expired:
        del _file_cache[fid]
    return len(expired)


def get_task(task_id: str) -> Optional[CheckTask]:
    """获取任务"""
    task = _check_tasks.get(task_id)
    if task and datetime.now() > task.expires_at:
        # 任务已过期
        del _check_tasks[task_id]
        return None
    return task


def save_task(task: CheckTask) -> None:
    """保存任务"""
    _check_tasks[task.task_id] = task


def delete_task(task_id: str) -> None:
    """删除任务"""
    if task_id in _check_tasks:
        del _check_tasks[task_id]


def cleanup_expired_tasks() -> int:
    """清理过期任务"""
    now = datetime.now()
    expired = [tid for tid, task in _check_tasks.items() if now > task.expires_at]
    for tid in expired:
        del _check_tasks[tid]
    return len(expired)


def parse_excel_file(file_content: bytes, file_name: str, sheet_name: str = None, header_row: int = 1) -> tuple:
    """
    解析 Excel 文件
    V1.3 扩展：支持指定Sheet和表头行
    
    Returns:
        (headers, data_rows)
    """
    try:
        if file_name.endswith('.xlsx'):
            engine = 'openpyxl'
        else:
            engine = 'xlrd'
        
        # V1.3: 支持指定Sheet
        read_params = {
            'io': BytesIO(file_content),
            'engine': engine,
            'header': header_row - 1  # pandas的header是0-indexed
        }
        
        if sheet_name:
            read_params['sheet_name'] = sheet_name
        
        df = pd.read_excel(**read_params)
        
        # 处理 NaN 值
        df = df.fillna('')
        
        headers = [str(col).strip() for col in df.columns]
        data_rows = df.to_dict('records')
        
        # 清理数据
        cleaned_rows = []
        for row in data_rows:
            cleaned_row = {}
            for key, value in row.items():
                clean_key = str(key).strip()
                if pd.isna(value):
                    cleaned_row[clean_key] = ''
                else:
                    cleaned_row[clean_key] = str(value).strip() if isinstance(value, str) else value
            cleaned_rows.append(cleaned_row)
        
        return headers, cleaned_rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析Excel文件失败: {str(e)}")


def auto_map_fields(file_headers: List[str], template_fields: List[Dict]) -> tuple:
    """
    自动映射字段
    
    Returns:
        (mapping, needs_manual_mapping)
    """
    mapping = {}
    template_names = {f['name']: f for f in template_fields}
    template_original = {f['original_name']: f for f in template_fields}
    
    unmatched_file = []
    unmatched_template = list(template_names.keys())
    
    for header in file_headers:
        # 精确匹配
        if header in template_names:
            mapping[header] = header
            if header in unmatched_template:
                unmatched_template.remove(header)
        elif header in template_original:
            field_name = template_original[header]['name']
            mapping[header] = field_name
            if field_name in unmatched_template:
                unmatched_template.remove(field_name)
        else:
            # 尝试模糊匹配（去除星号、空格）
            clean_header = header.replace('*', '').strip()
            matched = False
            for tname in list(unmatched_template):
                if clean_header == tname or clean_header.lower() == tname.lower():
                    mapping[header] = tname
                    unmatched_template.remove(tname)
                    matched = True
                    break
            if not matched:
                unmatched_file.append(header)
    
    # 检查是否有必填字段未映射
    required_unmatched = [
        f['name'] for f in template_fields 
        if f.get('required') and f['name'] in unmatched_template
    ]
    
    needs_manual = len(required_unmatched) > 0 or len(unmatched_file) > 0
    
    return mapping, needs_manual


def validate_row(row_data: Dict, field_mapping: Dict, template_fields: List[Dict]) -> Dict:
    """
    校验单行数据
    
    Returns:
        {row_index, data, status, issues}
    """
    # 构建字段配置映射
    field_configs = {f['name']: f for f in template_fields}
    
    all_issues = []
    
    # 对每个映射的字段进行校验
    for file_col, template_field in field_mapping.items():
        if template_field not in field_configs:
            continue
        
        value = row_data.get(file_col, '')
        config = field_configs[template_field]
        
        issues = validate_field(value, template_field, config)
        all_issues.extend(issues)
    
    # 确定行状态
    has_error = any(i.issue_type in ['required'] for i in all_issues)
    has_warning = any(i.issue_type not in ['required'] for i in all_issues)
    
    if has_error:
        status = 'error'
    elif has_warning:
        status = 'warning'
    else:
        status = 'valid'
    
    return {
        'status': status,
        'issues': [i.to_dict() for i in all_issues]
    }


def calculate_statistics(validation_results: List[Dict]) -> Dict:
    """计算统计信息"""
    total = len(validation_results)
    valid = sum(1 for r in validation_results if r['status'] == 'valid')
    warning = sum(1 for r in validation_results if r['status'] == 'warning')
    error = sum(1 for r in validation_results if r['status'] == 'error')
    
    # 计算可修复数量
    fixable = 0
    for r in validation_results:
        if any(i.get('fixable') for i in r.get('issues', [])):
            fixable += 1
    
    return {
        'total': total,
        'valid': valid,
        'warning': warning,
        'error': error,
        'fixable': fixable
    }


def start_check(
    db: Session,
    project_id: int,
    template_id: int,
    file: UploadFile = None,
    file_id: str = None,
    sheet_name: str = None,
    header_row: int = 1
) -> str:
    """
    开始校对任务
    V1.3 扩展：支持 file_id（从缓存获取）、sheet_name、header_row 参数
    
    Returns:
        task_id
    """
    # 获取模板
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 注意：模板现在是按项目组(team)管理的，不再检查 project_id
    # project_id 参数保留是为了兼容性，但不再用于验证
    
    # 解析模板字段
    fields_data = json.loads(template.fields) if template.fields else {"fields": []}
    template_fields = fields_data.get("fields", [])
    
    # V1.3: 支持从缓存获取文件或直接上传
    if file_id:
        # 从缓存获取文件
        cached = get_cached_file(file_id)
        if not cached:
            raise HTTPException(status_code=400, detail="文件缓存已过期，请重新上传")
        file_content = cached["content"]
        file_name = cached["file_name"]
    elif file:
        # 直接上传的文件
        try:
            file_content = file.file.read()
        except Exception:
            file.file.seek(0)
            file_content = file.file.read()
        file_name = file.filename
    else:
        raise HTTPException(status_code=400, detail="请提供文件或文件ID")
    
    # V1.3: 支持指定Sheet和表头行
    headers, data_rows = parse_excel_file(file_content, file_name, sheet_name, header_row)
    
    if not data_rows:
        raise HTTPException(status_code=400, detail="Excel文件没有数据")
    
    # 自动映射字段
    field_mapping, needs_mapping = auto_map_fields(headers, template_fields)
    
    # 创建任务
    task_id = str(uuid.uuid4())
    now = datetime.now()
    
    task = CheckTask(
        task_id=task_id,
        project_id=project_id,
        template_id=template_id,
        status='needs_mapping' if needs_mapping else 'processing',
        progress=0,
        original_file_name=file_name,
        original_data=[dict(row) for row in data_rows],  # 深拷贝
        current_data=data_rows,
        headers=headers,
        field_mapping=field_mapping,
        template_fields=template_fields,
        validation_results=[],
        statistics={},
        created_at=now,
        expires_at=now + timedelta(minutes=TASK_EXPIRE_MINUTES),
        sheet_name=sheet_name or "",
        header_row=header_row
    )
    
    # 如果不需要手动映射，直接执行校验
    if not needs_mapping:
        _execute_validation(task)
    
    save_task(task)
    return task_id


def _execute_validation(task: CheckTask) -> None:
    """执行校验"""
    task.status = 'processing'
    task.progress = 0
    
    validation_results = []
    total = len(task.current_data)
    
    for idx, row in enumerate(task.current_data):
        result = validate_row(row, task.field_mapping, task.template_fields)
        result['row_index'] = idx
        result['data'] = row
        validation_results.append(result)
        
        task.progress = int((idx + 1) / total * 100)
    
    task.validation_results = validation_results
    task.statistics = calculate_statistics(validation_results)
    task.status = 'done'
    task.progress = 100


def confirm_mapping(task_id: str, mapping: Dict[str, str]) -> bool:
    """确认字段映射"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    task.field_mapping = mapping
    _execute_validation(task)
    save_task(task)
    return True


def update_cell(task_id: str, row_index: int, field: str, value: Any) -> Dict:
    """更新单元格"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    if row_index < 0 or row_index >= len(task.current_data):
        raise HTTPException(status_code=400, detail="行索引无效")
    
    # 找到对应的文件列
    file_col = None
    for fc, tf in task.field_mapping.items():
        if tf == field:
            file_col = fc
            break
    
    if not file_col:
        # 直接使用字段名
        file_col = field
    
    # 更新数据
    task.current_data[row_index][file_col] = value
    
    # 重新校验该行
    result = validate_row(task.current_data[row_index], task.field_mapping, task.template_fields)
    result['row_index'] = row_index
    result['data'] = task.current_data[row_index]
    
    # 更新校验结果
    task.validation_results[row_index] = result
    task.statistics = calculate_statistics(task.validation_results)
    
    save_task(task)
    return result


def apply_fix(task_id: str, row_indices: List[int], fix_type: str) -> int:
    """
    应用修复
    
    Args:
        task_id: 任务ID
        row_indices: 要修复的行索引列表
        fix_type: 修复类型
    
    Returns:
        修复的数量
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    field_configs = {f['name']: f for f in task.template_fields}
    fixed_count = 0
    
    for row_idx in row_indices:
        if row_idx < 0 or row_idx >= len(task.current_data):
            continue
        
        row = task.current_data[row_idx]
        row_result = task.validation_results[row_idx]
        
        # 找到该行中可修复的问题
        for issue in row_result.get('issues', []):
            if not issue.get('fixable'):
                continue
            if fix_type and issue.get('issue_type') != fix_type:
                continue
            
            field_name = issue['field']
            
            # 找到对应的文件列
            file_col = None
            for fc, tf in task.field_mapping.items():
                if tf == field_name:
                    file_col = fc
                    break
            
            if not file_col:
                continue
            
            # 获取字段配置
            config = field_configs.get(field_name, {})
            
            # 修复值
            old_value = row.get(file_col, '')
            new_value = fix_field(old_value, config, issue['issue_type'])
            
            if new_value != old_value:
                row[file_col] = new_value
                fixed_count += 1
        
        # 重新校验该行
        result = validate_row(row, task.field_mapping, task.template_fields)
        result['row_index'] = row_idx
        result['data'] = row
        task.validation_results[row_idx] = result
    
    # 更新统计
    task.statistics = calculate_statistics(task.validation_results)
    save_task(task)
    
    return fixed_count


def reset_to_original(task_id: str) -> bool:
    """重置到原始数据"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    # 恢复原始数据
    task.current_data = [dict(row) for row in task.original_data]
    
    # 重新校验
    _execute_validation(task)
    save_task(task)
    
    return True


def get_task_result(task_id: str) -> Optional[Dict]:
    """获取任务结果"""
    task = get_task(task_id)
    if not task:
        return None
    
    return {
        'task_id': task.task_id,
        'status': task.status,
        'progress': task.progress,
        'original_file_name': task.original_file_name,
        'headers': task.headers,
        'field_mapping': task.field_mapping,
        'template_fields': task.template_fields,
        'needs_mapping': task.status == 'needs_mapping',
        'statistics': task.statistics,
        'rows': task.validation_results,
        'error_message': task.error_message
    }
