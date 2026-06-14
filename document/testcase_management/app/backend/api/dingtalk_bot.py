"""
钉钉机器人配置管理API
"""
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, DingtalkBot, Team
from auth import get_current_user
from pydantic import BaseModel, validator
from typing import Optional, List
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

DINGTALK_WEBHOOK_PREFIX = "https://oapi.dingtalk.com/robot/send"


class DingtalkBotCreate(BaseModel):
    name: str
    webhook_url: str
    security_type: str = "keyword"
    security_value: str
    team_id: int
    notification_types: List[str] = []
    is_active: bool = True

    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        if not v.startswith(DINGTALK_WEBHOOK_PREFIX):
            raise ValueError(f"Webhook URL必须以 {DINGTALK_WEBHOOK_PREFIX} 开头")
        return v

    @validator("security_type")
    def validate_security_type(cls, v):
        if v not in ("keyword", "sign"):
            raise ValueError("安全方式必须为 keyword 或 sign")
        return v


class DingtalkBotUpdate(BaseModel):
    name: Optional[str] = None
    webhook_url: Optional[str] = None
    security_type: Optional[str] = None
    security_value: Optional[str] = None
    team_id: Optional[int] = None
    notification_types: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        if v is not None and not v.startswith(DINGTALK_WEBHOOK_PREFIX):
            raise ValueError(f"Webhook URL必须以 {DINGTALK_WEBHOOK_PREFIX} 开头")
        return v

    @validator("security_type")
    def validate_security_type(cls, v):
        if v is not None and v not in ("keyword", "sign"):
            raise ValueError("安全方式必须为 keyword 或 sign")
        return v


def _generate_sign(secret: str, timestamp: str) -> str:
    """生成钉钉加签签名"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    return urllib.parse.quote_plus(base64.b64encode(hmac_code))


def _build_webhook_url(bot: DingtalkBot) -> str:
    """构建带签名的Webhook URL"""
    url = bot.webhook_url
    if bot.security_type == "sign":
        timestamp = str(round(time.time() * 1000))
        sign = _generate_sign(bot.security_value, timestamp)
        url = f"{url}&timestamp={timestamp}&sign={sign}"
    return url


def _send_dingtalk_message(bot: DingtalkBot, title: str, content: str) -> dict:
    """发送钉钉Markdown消息"""
    url = _build_webhook_url(bot)
    # 如果是关键词模式，确保标题包含关键词（标题不在消息卡片内显示）
    if bot.security_type == "keyword":
        if bot.security_value not in content and bot.security_value not in title:
            title = f"{title} {bot.security_value}"
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }
    
    try:
        resp = http_requests.post(url, json=payload, timeout=5)
        result = resp.json()
        if result.get("errcode") != 0:
            return {"success": False, "error": result.get("errmsg", "未知错误")}
        return {"success": True}
    except http_requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时（5秒）"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _bot_to_dict(bot: DingtalkBot, team_name: str = None) -> dict:
    """将DingtalkBot对象转为字典，隐藏敏感信息"""
    return {
        "id": bot.id,
        "name": bot.name,
        "webhook_url": bot.webhook_url[:60] + "***" if bot.webhook_url else "",
        "security_type": bot.security_type,
        "security_value": "***" if bot.security_value else "",
        "team_id": bot.team_id,
        "team_name": team_name,
        "notification_types": json.loads(bot.notification_types) if bot.notification_types else [],
        "is_active": bot.is_active,
        "created_by": bot.created_by,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


@router.get("")
def list_dingtalk_bots(
    req: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    team_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取钉钉机器人列表"""
    query = db.query(DingtalkBot)
    
    if search:
        query = query.filter(DingtalkBot.name.ilike(f"%{search}%"))
    if team_id is not None:
        query = query.filter(DingtalkBot.team_id == team_id)
    if is_active is not None:
        query = query.filter(DingtalkBot.is_active == is_active)
    
    total = query.count()
    bots = query.order_by(DingtalkBot.created_at.desc(), DingtalkBot.id.desc()).offset((page - 1) * size).limit(size).all()
    
    # 批量获取项目组名称
    team_ids = list(set(b.team_id for b in bots if b.team_id))
    teams = {t.id: t.name for t in db.query(Team).filter(Team.id.in_(team_ids)).all()} if team_ids else {}
    
    records = [_bot_to_dict(b, teams.get(b.team_id)) for b in bots]
    
    return {
        "code": 200,
        "message": "success",
        "data": {"records": records, "total": total, "page": page, "size": size}
    }


@router.post("")
def create_dingtalk_bot(
    req: Request,
    bot_data: DingtalkBotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建钉钉机器人"""
    # 名称唯一校验
    existing = db.query(DingtalkBot).filter(DingtalkBot.name == bot_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="机器人名称已存在")
    
    # 校验项目组存在
    team = db.query(Team).filter(Team.id == bot_data.team_id).first()
    if not team:
        raise HTTPException(status_code=400, detail="项目组不存在")
    
    db_bot = DingtalkBot(
        name=bot_data.name,
        webhook_url=bot_data.webhook_url,
        security_type=bot_data.security_type,
        security_value=bot_data.security_value,
        team_id=bot_data.team_id,
        notification_types=json.dumps(bot_data.notification_types),
        is_active=bot_data.is_active,
        created_by=current_user.id
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    log_operation(
        db=db, user_id=current_user.id, username=current_user.username,
        module=LogModule.SYSTEM, action=LogAction.CREATE,
        description=f"创建钉钉机器人：{bot_data.name}", request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": _bot_to_dict(db_bot, team.name)
    }


@router.put("/{bot_id}")
def update_dingtalk_bot(
    req: Request,
    bot_id: int,
    bot_data: DingtalkBotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新钉钉机器人"""
    db_bot = db.query(DingtalkBot).filter(DingtalkBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    update_data = bot_data.dict(exclude_unset=True)
    
    # 名称唯一校验
    if "name" in update_data:
        existing = db.query(DingtalkBot).filter(
            DingtalkBot.name == update_data["name"],
            DingtalkBot.id != bot_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="机器人名称已存在")
    
    # 项目组校验
    if "team_id" in update_data:
        team = db.query(Team).filter(Team.id == update_data["team_id"]).first()
        if not team:
            raise HTTPException(status_code=400, detail="项目组不存在")
    
    # notification_types 序列化
    if "notification_types" in update_data:
        update_data["notification_types"] = json.dumps(update_data["notification_types"])
    
    for field, value in update_data.items():
        setattr(db_bot, field, value)
    
    db.commit()
    db.refresh(db_bot)
    
    team = db.query(Team).filter(Team.id == db_bot.team_id).first()
    
    log_operation(
        db=db, user_id=current_user.id, username=current_user.username,
        module=LogModule.SYSTEM, action=LogAction.UPDATE,
        description=f"更新钉钉机器人：{db_bot.name}", request=req
    )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": _bot_to_dict(db_bot, team.name if team else None)
    }


@router.delete("/{bot_id}")
def delete_dingtalk_bot(
    req: Request,
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除钉钉机器人"""
    db_bot = db.query(DingtalkBot).filter(DingtalkBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    bot_name = db_bot.name
    db.delete(db_bot)
    db.commit()
    
    log_operation(
        db=db, user_id=current_user.id, username=current_user.username,
        module=LogModule.SYSTEM, action=LogAction.DELETE,
        description=f"删除钉钉机器人：{bot_name}", request=req
    )
    
    return {"code": 200, "message": "删除成功", "data": None}


@router.put("/{bot_id}/toggle")
def toggle_dingtalk_bot(
    req: Request,
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换钉钉机器人启用状态"""
    db_bot = db.query(DingtalkBot).filter(DingtalkBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    db_bot.is_active = not db_bot.is_active
    db.commit()
    
    status_text = "启用" if db_bot.is_active else "禁用"
    log_operation(
        db=db, user_id=current_user.id, username=current_user.username,
        module=LogModule.SYSTEM, action=LogAction.UPDATE,
        description=f"{status_text}钉钉机器人：{db_bot.name}", request=req
    )
    
    return {"code": 200, "message": f"{status_text}成功", "data": {"is_active": db_bot.is_active}}


@router.post("/{bot_id}/test")
def test_dingtalk_bot(
    req: Request,
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试钉钉机器人发送"""
    db_bot = db.query(DingtalkBot).filter(DingtalkBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    title = "测试用例管理平台 - 连接测试"
    content = (
        "### 🔔 钉钉机器人连接测试\n\n"
        f"**机器人名称**: {db_bot.name}\n\n"
        f"**测试人**: {current_user.username}\n\n"
        f"**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "---\n\n"
        "✅ 如果您看到此消息，说明机器人配置正确。"
    )
    
    result = _send_dingtalk_message(db_bot, title, content)
    
    if result["success"]:
        return {"code": 200, "message": "测试消息发送成功", "data": None}
    else:
        raise HTTPException(status_code=400, detail=f"发送失败：{result['error']}")
