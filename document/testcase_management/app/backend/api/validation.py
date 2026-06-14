from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user
import pandas as pd
import re
from typing import List, Dict
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

def validate_required_field(value, field_name: str, row_num: int) -> List[Dict]:
    """验证必填字段"""
    errors = []
    if pd.isna(value) or str(value).strip() == '':
        errors.append({
            "row": row_num,
            "field": field_name,
            "message": f"{field_name}不能为空",
            "severity": "error"
        })
    return errors

def validate_length(value, field_name: str, max_length: int, row_num: int) -> List[Dict]:
    """验证字段长度"""
    errors = []
    if not pd.isna(value) and len(str(value)) > max_length:
        errors.append({
            "row": row_num,
            "field": field_name,
            "message": f"{field_name}长度超过{max_length}个字符",
            "severity": "error"
        })
    return errors

def validate_step_format(steps: str, row_num: int) -> List[Dict]:
    """验证测试步骤格式"""
    warnings = []
    if pd.isna(steps):
        return warnings
    
    steps_str = str(steps)
    # 检查是否有序号
    has_numbers = bool(re.search(r'^\s*\d+[.、]', steps_str, re.MULTILINE))
    if not has_numbers and len(steps_str) > 20:
        warnings.append({
            "row": row_num,
            "field": "测试步骤",
            "message": "建议使用序号标注步骤（如：1. 2. 3.）",
            "severity": "warning"
        })
    
    # 检查步骤是否过短
    if len(steps_str.strip()) < 10:
        warnings.append({
            "row": row_num,
            "field": "测试步骤",
            "message": "测试步骤描述过于简单，建议详细说明",
            "severity": "warning"
        })
    
    return warnings

def validate_expected_result(result: str, row_num: int) -> List[Dict]:
    """验证预期结果"""
    warnings = []
    if pd.isna(result):
        return warnings
    
    result_str = str(result).strip()
    
    # 检查是否过于模糊
    vague_words = ['正常', '成功', '正确', '可以', '能够']
    if len(result_str) < 15 and any(word in result_str for word in vague_words):
        warnings.append({
            "row": row_num,
            "field": "预期结果",
            "message": "预期结果描述过于模糊，建议明确具体的结果",
            "severity": "warning"
        })
    
    return warnings

@router.post("/validate")
async def validate_testcases(
    req: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """校对Excel测试用例"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        # 读取文件内容到内存
        contents = await file.read()
        
        # 使用 BytesIO 包装内容
        import io
        file_like = io.BytesIO(contents)
        
        # 读取Excel文件
        df = pd.read_excel(file_like)
        
        # 检查必需的列
        required_columns = ['用例名称', '测试步骤', '预期结果']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "code": 400,
                "message": f"缺少必需的列: {', '.join(missing_columns)}",
                "data": None
            }
        
        errors = []
        warnings = []
        valid_cases = 0
        
        # 逐行验证
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel行号（从2开始，因为第1行是表头）
            row_errors = []
            row_warnings = []
            
            # 验证用例名称
            row_errors.extend(validate_required_field(row.get('用例名称'), '用例名称', row_num))
            row_errors.extend(validate_length(row.get('用例名称'), '用例名称', 255, row_num))
            
            # 验证测试步骤
            row_errors.extend(validate_required_field(row.get('测试步骤'), '测试步骤', row_num))
            row_warnings.extend(validate_step_format(row.get('测试步骤'), row_num))
            
            # 验证预期结果
            row_errors.extend(validate_required_field(row.get('预期结果'), '预期结果', row_num))
            row_warnings.extend(validate_expected_result(row.get('预期结果'), row_num))
            
            errors.extend(row_errors)
            warnings.extend(row_warnings)
            
            if len(row_errors) == 0:
                valid_cases += 1
        
        total_cases = len(df)
        is_valid = len(errors) == 0
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "is_valid": is_valid,
                "total_cases": total_cases,
                "valid_cases": valid_cases,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors,
                "warnings": warnings
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")
