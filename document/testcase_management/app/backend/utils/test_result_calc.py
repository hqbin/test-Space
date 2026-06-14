"""
测试结果统计计算工具

统一 Passing rate 公式和 MpList 测试统计解析。
所有生成报告的地方（snapshot、实时计算、PDF导出、Excel导出、前端预览）都使用此模块。

Passing rate 公式：
  PASS / (总用例 - NA - NT - 协测)

MpList 模块统计：
  从 MpList 的 "xx测试" 列（排除"测试备注"列）中提取测试结果，
  清洗符号后统计 PASS / FAIL / BLOCK / NT / NA / 协测。
"""

import re
import logging

logger = logging.getLogger(__name__)


def normalize_mplist_result(raw_value: str) -> str:
    """清洗 MpList 测试结果值，去除符号，返回标准化结果。
    
    已知值示例：
      '✓ Pass' -> 'PASS'
      '◐ NT' -> 'NT'
      '未测试' -> 'NT'  (未测试等同于NT)
      '协测' -> '协测'
      '✗ Fail' / 'Fail' -> 'FAIL'
      'Block' -> 'BLOCK'
      'NA' / 'N/A' -> 'NA'
      '-' / '' -> None (忽略，不计入统计)
    """
    if not raw_value:
        return None
    s = raw_value.strip()
    if not s or s == '-':
        return None
    
    # 去除常见前缀符号：✓ ✗ ◐ ● ○ △ ▲ × ★ 等
    s_clean = re.sub(r'^[✓✗◐●○△▲×★☆✔✘⊙◉►▶▷▸☑☒□■◻◼\s]+', '', s).strip()
    
    low = s_clean.lower()
    
    if low in ('pass', 'passed', '通过'):
        return 'PASS'
    elif low in ('fail', 'failed', '失败'):
        return 'FAIL'
    elif low in ('block', 'blocked', '阻塞'):
        return 'BLOCK'
    elif low in ('nt', 'not tested', '未测试', 'not test'):
        return 'NT'
    elif low in ('na', 'n/a', '不适用'):
        return 'NA'
    elif low in ('协测',):
        return '协测'
    
    # 如果原始值包含关键字（处理如 "Pass" 带其他符号的情况）
    raw_low = raw_value.strip().lower()
    if 'pass' in raw_low:
        return 'PASS'
    elif 'fail' in raw_low:
        return 'FAIL'
    elif 'block' in raw_low:
        return 'BLOCK'
    elif 'nt' in raw_low or '未测试' in raw_value:
        return 'NT'
    elif 'na' in raw_low or 'n/a' in raw_low:
        return 'NA'
    elif '协测' in raw_value:
        return '协测'
    
    # 无法识别的值，记录日志，忽略
    logger.warning(f"MpList: 无法识别的测试结果值: [{raw_value}]")
    return None


def parse_mplist_test_stats(mplist_data: dict) -> dict:
    """从 MpList 数据中解析测试统计。
    
    Args:
        mplist_data: {'headers': [...], 'rows': [[...], ...]}
    
    Returns:
        {
            'has_stats': True/False,
            'test_col_name': 'xx测试',  # 找到的测试列名
            'pass': int,
            'fail': int,
            'block': int,
            'nt': int,
            'na': int,
            'assist': int,  # 协测数量
            'has_assist': True/False,  # 是否有协测结果
            'total_rows': int,  # MpList总行数
            'test_cases': int,  # 有效用例数 = total - NA - 协测
            'passing_rate': float  # PASS / test_cases * 100
        }
    """
    if not mplist_data or not isinstance(mplist_data, dict):
        return {'has_stats': False}
    
    headers = mplist_data.get('headers', [])
    rows = mplist_data.get('rows', [])
    
    if not headers or not rows:
        return {'has_stats': False}
    
    # 找到 "xx测试" 列（排除 "测试备注"）
    # 规则：列名以"测试"结尾，但不是"测试备注"，只取第一个匹配的
    test_col_idx = None
    test_col_name = None
    for idx, h in enumerate(headers):
        h_str = str(h).strip()
        if h_str.endswith('测试') and h_str != '测试备注':
            test_col_idx = idx
            test_col_name = h_str
            break
    
    if test_col_idx is None:
        logger.info("MpList: 未找到 xx测试 列，跳过统计")
        return {'has_stats': False}
    
    logger.info(f"MpList: 找到测试列 [{test_col_name}] (列索引 {test_col_idx})")
    
    # 统计各结果
    stats = {'PASS': 0, 'FAIL': 0, 'BLOCK': 0, 'NT': 0, 'NA': 0, '协测': 0}
    total_counted = 0
    
    for row in rows:
        if test_col_idx >= len(row):
            continue
        raw_val = row[test_col_idx]
        result = normalize_mplist_result(raw_val)
        if result is None:
            continue
        total_counted += 1
        if result in stats:
            stats[result] += 1
    
    has_assist = stats['协测'] > 0
    # 有效用例数 = 总数 - NA - 协测
    effective = total_counted - stats['NA'] - stats['协测']
    passing_rate = (stats['PASS'] / effective * 100) if effective > 0 else 0
    
    return {
        'has_stats': True,
        'test_col_name': test_col_name,
        'pass': stats['PASS'],
        'fail': stats['FAIL'],
        'block': stats['BLOCK'],
        'nt': stats['NT'],
        'na': stats['NA'],
        'assist': stats['协测'],
        'has_assist': has_assist,
        'total_rows': total_counted,
        'test_cases': effective,
        'passing_rate': passing_rate
    }
