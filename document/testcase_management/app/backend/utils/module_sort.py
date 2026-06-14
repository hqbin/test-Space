"""模块排序工具 - 提供基于sort_order的模块排序功能"""
from sqlalchemy.orm import Session
from models import Module, TestCase


def get_module_sort_map(db: Session, project_ids):
    """构建模块路径到排序键的映射字典。
    返回 dict: {path: sort_key}，sort_key格式如 "0000000010.0000000020"
    """
    if isinstance(project_ids, int):
        project_ids = [project_ids]
    if not project_ids:
        return {}

    modules = db.query(Module).filter(Module.project_id.in_(project_ids)).all()
    if not modules:
        return {}

    mod_map = {m.id: m for m in modules}
    sort_key_cache = {}

    def get_sort_key(module):
        if module.id in sort_key_cache:
            return sort_key_cache[module.id]
        # 使用 sort_order + id 构建排序键，与侧边栏树的 (sort_order, id) 排序一致
        sort_str = str(module.sort_order or 0).zfill(10) + '_' + str(module.id).zfill(10)
        if module.parent_id and module.parent_id in mod_map:
            parent_key = get_sort_key(mod_map[module.parent_id])
            sort_str = parent_key + '.' + sort_str
        sort_key_cache[module.id] = sort_str
        return sort_str

    def get_full_path(module):
        parts = [module.name]
        current = module
        while current.parent_id and current.parent_id in mod_map:
            current = mod_map[current.parent_id]
            parts.insert(0, current.name)
        return '/'.join(parts)

    path_to_sort = {}
    for m in modules:
        path_to_sort[get_full_path(m)] = get_sort_key(m)
    return path_to_sort


def build_module_sort_key_expr(db: Session, project_ids):
    """构建SQLAlchemy case()表达式，用于order_by按模块sort_order排序。
    
    使用 COALESCE 确保子模块能 fallback 到主模块的排序
    """
    from sqlalchemy import case, literal, func

    path_to_sort = get_module_sort_map(db, project_ids)
    if not path_to_sort:
        return TestCase.module.asc().nullslast()

    # 构建 case() 表达式：
    # 1. 精确匹配每个已知模块路径（子模块路径更长，优先匹配）
    # 2. LIKE 回退：未识别的子路径仍归入其主模块排序区间
    
    # 按路径深度降序排列（子模块在前），确保精确匹配优先
    sorted_paths = sorted(path_to_sort.items(), key=lambda x: -len(x[0].split('/')))
    
    all_whens = []
    # 精确匹配
    for path, sort_key in sorted_paths:
        all_whens.append((TestCase.module == path, literal(sort_key)))
    
    # LIKE 回退：对每个已知路径，匹配其下的未知子路径
    # 例如模块 "ISDB" sort_key="0000000010_0000000005"，
    # 则 module LIKE 'ISDB/%' 的用例也归入该排序区间（追加 .9999999999 排在已知子模块之后）
    seen_prefixes = set()
    for path, sort_key in sorted_paths:
        prefix = path
        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            all_whens.append((
                TestCase.module.like(prefix + '/%'),
                literal(sort_key + '.9999999999_9999999999')
            ))
    
    return case(*all_whens, else_=literal('9999999999')).asc()


def sort_module_paths(db: Session, project_ids, paths):
    """对模块路径列表按sort_order排序，返回排序后的列表。
    用于Python层面的列表排序（如报告中的模块统计）。
    """
    path_to_sort = get_module_sort_map(db, project_ids)
    return sorted(paths, key=lambda p: path_to_sort.get(p, '9999999999'))
