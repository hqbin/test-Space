from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import json
import shutil

from database import get_db
from auth import get_current_user
from models import User

router = APIRouter(prefix="/apk", tags=["APK管理"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "aivoice", "apk")
SIGNED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "aivoice", "apk-signed")


def _ensure_dirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(SIGNED_DIR, exist_ok=True)


@router.post("/upload")
async def upload_apk(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_dirs()
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {
        "code": 200, "message": "success",
        "data": {
            "fileName": file.filename,
            "fileSize": len(content),
            "filePath": file_path,
        },
    }


@router.get("/list")
def list_apk_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_dirs()
    files = []
    for f in os.listdir(UPLOAD_DIR):
        fp = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(fp):
            files.append({
                "fileName": f,
                "fileSize": os.path.getsize(fp),
                "filePath": fp,
                "updatedAt": os.path.getmtime(fp),
            })
    files.sort(key=lambda x: x["updatedAt"], reverse=True)
    return {"code": 200, "message": "success", "data": files}


@router.delete("/{file_name}")
def delete_apk(
    file_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_dirs()
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    signed_path = os.path.join(SIGNED_DIR, file_name)
    if os.path.exists(signed_path):
        os.remove(signed_path)
    return {"code": 200, "message": "success", "message": "删除成功"}
