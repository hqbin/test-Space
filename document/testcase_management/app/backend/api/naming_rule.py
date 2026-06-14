"""
命名规则配置接口 - 用例编号命名规则的查看和编辑
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import SystemConfig, User
from auth import get_current_user, has_permission
from utils.logger import log_operation, LogAction, LogModule
import json

router = APIRouter()

NAMING_RULE_KEY = "naming_rule_content"

# 默认命名规则内容
DEFAULT_NAMING_RULE = {
    "format_description": "用例编号命名格式：用例库代号_父模块代号_XXXX\n比如：OS10_ADV_0001\n备注：如果父模块无TAG，则用例编号命名格式：用例库代号_XXXX，比如OS10_0001",
    "project_codes": [
        {"name": "WhaleOS 10", "code": "OSF10"},
        {"name": "STB_Fulltest", "code": "STBF"},
        {"name": "STB_Compatibility", "code": "STBC"},
        {"name": "STB_Stress test", "code": "STBST"},
        {"name": "STB_Performance", "code": "STBP"},
        {"name": "AOSP(whale tv power)", "code": "WP"},
        {"name": "TV casting", "code": "TC"},
        {"name": "WhaleOS Stress TestCase", "code": "OS10S"},
        {"name": "WhaleOS_LiveTV", "code": "OSF"},
        {"name": "Whale App", "code": "WAPP"},
        {"name": "WhaleOS_客制化测试用例", "code": "OS10C"},
        {"name": "WhaleOS_SmartTV", "code": "OS10F"},
        {"name": "WhaleOS Quick TestCase", "code": "QT"}
    ],
    "module_codes": [
        {"name": "Global", "code": "GLO", "logic": "Global 前 3 字母，全球通用无歧义"},
        {"name": "开机流程", "code": "BOO", "logic": "Boot Operation（开机操作），贴合开机流程核心"},
        {"name": "UserCenter", "code": "USR", "logic": "User 前 3 字母，用户中心核心标识"},
        {"name": "Search", "code": "SEA", "logic": "Search 前 3 字母，搜索模块通用缩写"},
        {"name": "Home", "code": "HOM", "logic": "Home 前 3 字母，首页模块标准缩写"},
        {"name": "Free TV", "code": "FRE", "logic": "Free 前 3 字母，免费电视模块标识"},
        {"name": "Discovery", "code": "DIS", "logic": "Discovery 前 3 字母，发现页通用缩写"},
        {"name": "Apps", "code": "APP", "logic": "Apps 完整 3 字母，应用模块标准缩写"},
        {"name": "Setting", "code": "SET", "logic": "Setting 前 3 字母，设置模块通用缩写"},
        {"name": "OTA", "code": "OTA", "logic": "保留原缩写，OTA 升级模块无歧义"},
        {"name": "Voice", "code": "VOI", "logic": "Voice 前 3 字母，语音模块通用缩写"},
        {"name": "数据埋点", "code": "PNT", "logic": "Point（埋点），贴合数据埋点核心"},
        {"name": "TV_Casting", "code": "CAS", "logic": "Casting（投屏），投屏模块行业通用缩写"},
        {"name": "遥控器", "code": "REM", "logic": "Remote（遥控器），遥控器模块标准缩写"},
        {"name": "键鼠", "code": "KBM", "logic": "Keyboard Mouse（键盘鼠标），键鼠模块精准标识"},
        {"name": "Files", "code": "FIL", "logic": "Files 前 3 字母，文件模块通用缩写"},
        {"name": "PID", "code": "PID", "logic": "保留原缩写，PID 模块无歧义"},
        {"name": "AD", "code": "ADV", "logic": "Advertisement（广告），避免与单字母 AD 混淆"},
        {"name": "无网_断网", "code": "NET", "logic": "Network（网络），无网/断网网络异常场景标识"},
        {"name": "Hotel Mode", "code": "HOT", "logic": "Hotel 前 3 字母，酒店模式模块标识"},
        {"name": "redemption campaign", "code": "RDM", "logic": "Redemption（兑换），兑换活动模块标识"},
        {"name": "Parent Control", "code": "PAR", "logic": "Parent 前 3 字母，家长控制模块通用缩写"},
        {"name": "ERP弹窗", "code": "ERP", "logic": "保留原缩写，ERP 弹窗模块无歧义"},
        {"name": "Files TTS", "code": "TTS", "logic": "保留原缩写，TTS 语音播报模块无歧义"},
        {"name": "多类型校验", "code": "MTY", "logic": "MultiType（多类型），多类型校验模块标识"},
        {"name": "Media Service", "code": "MED", "logic": "Media 前 3 字母，媒体服务模块通用缩写"},
        {"name": "Whaletv+ CIS", "code": "WHC", "logic": "Whaletv CIS，WhaleTV+ CIS 模块标识"},
        {"name": "Security Solution", "code": "SEC", "logic": "Security 前 3 字母，安全方案模块通用缩写"},
        {"name": "TV LOCK", "code": "LCK", "logic": "Lock（锁定），电视锁模块精准标识"},
        {"name": "音视频传输", "code": "AVT", "logic": "Audio Video Transmission，音视频传输模块精准标识"},
        {"name": "Launcher", "code": "LAU", "logic": "Launcher 缩写"},
        {"name": "Store", "code": "STO", "logic": "Store 缩写"},
        {"name": "天气", "code": "WEA", "logic": "Weather 缩写"},
        {"name": "通知", "code": "NOT", "logic": "Notification 缩写"},
        {"name": "应用锁", "code": "APL", "logic": "App Lock 缩写"},
        {"name": "定时刷新", "code": "REF", "logic": "Refresh 缩写"},
        {"name": "热更新", "code": "HTU", "logic": "Hot Update 缩写"},
        {"name": "原生TOU", "code": "NTU", "logic": "Native TOU 缩写"},
        {"name": "非原生TOU", "code": "FTU", "logic": "Foreign TOU 缩写"},
        {"name": "主题", "code": "THE", "logic": "Theme 缩写"}
    ]
}


@router.get("")
def get_naming_rule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取命名规则配置"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == NAMING_RULE_KEY).first()
    if config and config.config_value:
        try:
            data = json.loads(config.config_value)
            return {"code": 200, "message": "success", "data": data, "updated_by": config.updated_by, "updated_at": config.updated_at}
        except json.JSONDecodeError:
            pass
    # 返回默认值
    return {"code": 200, "message": "success", "data": DEFAULT_NAMING_RULE, "updated_by": None, "updated_at": None}


class NamingRuleUpdate(BaseModel):
    data: dict  # 完整的命名规则JSON


@router.put("")
def update_naming_rule(
    req: Request,
    body: NamingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新命名规则配置（需要 projects.editNamingRule 权限）"""
    if not has_permission(current_user, db, 'projects.editNamingRule'):
        raise HTTPException(status_code=403, detail="没有编辑命名规则的权限")

    config = db.query(SystemConfig).filter(SystemConfig.config_key == NAMING_RULE_KEY).first()
    if not config:
        config = SystemConfig(config_key=NAMING_RULE_KEY)
        db.add(config)

    config.config_value = json.dumps(body.data, ensure_ascii=False)
    config.updated_by = current_user.id
    db.commit()

    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.PROJECTS,
        action=LogAction.UPDATE,
        description="更新用例编号命名规则",
        request=req
    )

    return {"code": 200, "message": "更新成功"}
