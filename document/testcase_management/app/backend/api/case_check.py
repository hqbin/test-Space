"""
用例校对 API
V1.3 - 支持多Sheet处理
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from io import BytesIO
import pandas as pd

from database import get_db
from auth import get_current_user
from models import User
from services import case_check_service
from utils.sheet_parser import parse_all_sheets, detect_recommended_sheet, detect_header_row

router = APIRouter()


class MappingRequest(BaseModel):
    """字段映射请求"""
    mapping: dict


class UpdateCellRequest(BaseModel):
    """更新单元格请求"""
    row_index: int
    field: str
    value: str


class FixRequest(BaseModel):
    """修复请求"""
    row_indices: List[int]
    fix_type: Optional[str] = None  # 不指定则修复所有可修复问题


@router.post("/projects/{project_id}/case/check/parse-sheets")
def parse_sheets(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    解析Excel文件的所有Sheet
    V1.3 新增接口
    """
    import traceback
    import uuid
    try:
        # 读取文件内容
        file_content = file.file.read()
        file.file.seek(0)
        
        # 解析所有Sheet
        sheets = parse_all_sheets(file_content, file.filename)
        
        # 检测推荐Sheet
        recommended = detect_recommended_sheet(sheets)
        
        # 生成临时文件ID（用于后续校对）
        file_id = str(uuid.uuid4())
        
        # 缓存文件内容（用于后续校对）
        case_check_service.cache_file(file_id, file_content, file.filename)
        
        # 转换为响应格式
        sheets_data = []
        for sheet in sheets:
            # 检测表头行
            header_row = detect_header_row(sheet.preview_rows) if sheet.preview_rows else 1
            
            sheets_data.append({
                "name": sheet.name,
                "row_count": sheet.row_count,
                "column_count": sheet.column_count,
                "preview_rows": sheet.preview_rows,
                "auto_recommend": sheet.auto_recommend,
                "recommend_reason": sheet.recommend_reason,
                "detected_header_row": header_row
            })
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "file_id": file_id,
                "file_name": file.filename,
                "sheet_count": len(sheets),
                "sheets": sheets_data,
                "recommended_sheet": recommended
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"解析Sheet失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"解析Sheet失败: {str(e)}")


@router.post("/projects/{project_id}/case/check")
def start_check(
    project_id: int,
    template_id: int = Form(...),
    file: UploadFile = File(None),
    file_id: str = Form(None),
    sheet_name: str = Form(None),
    header_row: int = Form(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    开始校对任务
    V1.3 扩展：支持 file_id（从缓存获取）、sheet_name、header_row 参数
    """
    import traceback
    try:
        task_id = case_check_service.start_check(
            db=db,
            project_id=project_id,
            template_id=template_id,
            file=file,
            file_id=file_id,
            sheet_name=sheet_name,
            header_row=header_row
        )
        return {"code": 200, "message": "success", "data": {"task_id": task_id, "status": "processing"}}
    except HTTPException:
        raise
    except Exception as e:
        print(f"校对任务创建失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"校对任务创建失败: {str(e)}")


@router.get("/case/check/{task_id}")
def get_check_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取校对结果"""
    result = case_check_service.get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return {"code": 200, "message": "success", "data": result}


@router.post("/case/check/{task_id}/mapping")
def confirm_mapping(
    task_id: str,
    data: MappingRequest,
    current_user: User = Depends(get_current_user)
):
    """确认字段映射"""
    case_check_service.confirm_mapping(task_id, data.mapping)
    return {"code": 200, "message": "success", "data": {"message": "映射已确认，开始校验"}}


@router.post("/case/check/{task_id}/update")
def update_cell(
    task_id: str,
    data: UpdateCellRequest,
    current_user: User = Depends(get_current_user)
):
    """更新单元格"""
    result = case_check_service.update_cell(
        task_id=task_id,
        row_index=data.row_index,
        field=data.field,
        value=data.value
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/case/check/{task_id}/fix")
def apply_fix(
    task_id: str,
    data: FixRequest,
    current_user: User = Depends(get_current_user)
):
    """应用修复"""
    fixed_count = case_check_service.apply_fix(
        task_id=task_id,
        row_indices=data.row_indices,
        fix_type=data.fix_type
    )
    return {"code": 200, "message": "success", "data": {"fixed_count": fixed_count}}


@router.post("/case/check/{task_id}/reset")
def reset_to_original(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """重置到原始数据"""
    case_check_service.reset_to_original(task_id)
    return {"code": 200, "message": "success", "data": {"message": "已重置到原始数据"}}


@router.get("/case/check/{task_id}/export")
def export_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """导出修正后的Excel文件"""
    import traceback
    try:
        task = case_check_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在或已过期")
        
        # 构建反向映射：原始列名 -> 模板字段名
        reverse_mapping = {v: k for k, v in task.field_mapping.items()}
        
        # 使用映射后的表头导出
        export_data = []
        for row in task.current_data:
            if isinstance(row, dict):
                mapped_row = {}
                for original_col, value in row.items():
                    # 如果该列有映射，使用映射后的字段名
                    mapped_col = task.field_mapping.get(original_col, original_col)
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        mapped_row[mapped_col] = value if value is not None else ''
                    else:
                        mapped_row[mapped_col] = str(value)
                export_data.append(mapped_row)
        
        # 创建 DataFrame
        df = pd.DataFrame(export_data)
        
        # 按映射后的字段顺序排列列
        mapped_headers = [task.field_mapping.get(h, h) for h in task.headers]
        ordered_columns = [col for col in mapped_headers if col in df.columns]
        if ordered_columns:
            df = df[ordered_columns]
        
        # 生成 Excel 文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 使用原始Sheet名或默认Sheet1
            sheet_name = task.sheet_name if task.sheet_name else 'Sheet1'
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        
        # 生成文件名 - 包含Sheet名
        from urllib.parse import quote
        original_name = task.original_file_name.rsplit('.', 1)[0]
        if task.sheet_name:
            export_name = f"{original_name}_{task.sheet_name}_校对后.xlsx"
        else:
            export_name = f"{original_name}_校对后.xlsx"
        encoded_name = quote(export_name)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"导出失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
