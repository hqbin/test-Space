"""
测试用例工具函数

提供统一的测试用例数据处理方法，避免在不同模块中重复代码和出现不一致的问题
"""

import json
from typing import List, Tuple


def parse_steps_and_expected(steps_json: str, expected_result_json: str = None) -> Tuple[List[str], List[str]]:
    """
    解析测试用例的操作步骤和预期结果
    
    数据库中的steps字段存储格式：
    [
        {"step": "1. 打开应用", "expected": "1. 应用正常启动"},
        {"step": "2. 点击按钮", "expected": "2. 按钮响应正常"}
    ]
    
    注意：如果数据库中没有序号，会自动添加序号
    
    Args:
        steps_json: steps字段的JSON字符串
        expected_result_json: expected_result字段的JSON字符串（可选，用于向后兼容）
    
    Returns:
        (steps_list, expected_list): 操作步骤列表和预期结果列表
    """
    steps_list = []
    expected_list = []
    
    try:
        if steps_json:
            steps_data = json.loads(steps_json) if isinstance(steps_json, str) else steps_json
            
            if isinstance(steps_data, list):
                for idx, item in enumerate(steps_data, start=1):
                    if isinstance(item, dict):
                        # 提取操作步骤
                        step_str = item.get('step', '').strip()
                        if step_str:
                            # 如果没有序号前缀，自动添加
                            if not (step_str[0].isdigit() or step_str.startswith('步骤')):
                                step_str = f"{idx}. {step_str}"
                            steps_list.append(step_str)
                        
                        # 提取预期结果
                        expected_str = item.get('expected', '').strip()
                        if expected_str:
                            # 如果没有序号前缀，自动添加
                            if not (expected_str[0].isdigit() or expected_str.startswith('预期')):
                                expected_str = f"{idx}. {expected_str}"
                            expected_list.append(expected_str)
        
        # 如果expected_result字段有单独的数据，使用它（向后兼容旧数据）
        if not expected_list and expected_result_json:
            expected_data = json.loads(expected_result_json) if isinstance(expected_result_json, str) else expected_result_json
            
            if isinstance(expected_data, list):
                for item in expected_data:
                    if isinstance(item, dict):
                        exp_str = item.get('expected', '').strip()
                    else:
                        exp_str = str(item).strip()
                    
                    if exp_str:
                        expected_list.append(exp_str)
    
    except Exception as e:
        # 如果解析失败，返回空列表
        print(f"解析步骤数据失败: {e}")
        return [], []
    
    return steps_list, expected_list


def format_steps_for_excel(steps_list: List[str]) -> str:
    """
    格式化操作步骤为Excel格式（每行一个步骤）
    
    Args:
        steps_list: 操作步骤列表
    
    Returns:
        格式化后的文本，使用换行符分隔
    """
    return "\n".join(steps_list) if steps_list else ""


def format_steps_for_pdf(steps_list: List[str]) -> str:
    """
    格式化操作步骤为PDF格式（使用<br/>标签）
    
    Args:
        steps_list: 操作步骤列表
    
    Returns:
        格式化后的HTML文本，使用<br/>分隔
    """
    return "<br/>".join(steps_list) if steps_list else "-"


def format_steps_for_display(steps_list: List[str]) -> str:
    """
    格式化操作步骤为前端显示格式
    
    Args:
        steps_list: 操作步骤列表
    
    Returns:
        格式化后的文本
    """
    return "\n".join(steps_list) if steps_list else ""


# 使用示例：
# 
# from utils.testcase_utils import parse_steps_and_expected, format_steps_for_excel
# 
# # 解析数据
# steps_list, expected_list = parse_steps_and_expected(testcase.steps, testcase.expected_result)
# 
# # 格式化为Excel
# steps_text = format_steps_for_excel(steps_list)
# expected_text = format_steps_for_excel(expected_list)
# 
# # 格式化为PDF
# steps_html = format_steps_for_pdf(steps_list)
# expected_html = format_steps_for_pdf(expected_list)
