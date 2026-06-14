from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceSetting


class SettingUpdate(BaseModel):
    value: str


router = APIRouter(prefix="/settings", tags=["设置"])


@router.get("/{key}")
def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(AiVoiceSetting).filter(AiVoiceSetting.key == key).first()
    if not row:
        return {"code": 200, "message": "success", "data": None}
    return {"code": 200, "message": "success", "data": row.value}


@router.put("/{key}")
def update_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(AiVoiceSetting).filter(AiVoiceSetting.key == key).first()
    if row:
        row.value = body.value
    else:
        db.add(AiVoiceSetting(key=key, value=body.value))
    db.commit()
    return {"code": 200, "message": "保存成功"}
