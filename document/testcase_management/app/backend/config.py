import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    # 数据库配置 - PostgreSQL
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:whaletv%40admin.com!@172.16.60.161:5432/testcase_platform")
    
    # JWT配置
    SECRET_KEY = os.getenv("SECRET_KEY", "testplatform-secret-key-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "8640"))
    
    # 文件上传配置
    UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))
    
    # CORS配置
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:2026,http://172.16.52.62:2026,http://172.16.60.161:2026").split(",")
    
    # 前端地址（用于钉钉通知中的跳转链接）
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://tms.zeasn.com")
    
    # Zmind配置
    ZMIND_API_KEY = os.getenv("ZMIND_API_KEY", "51be09c67413a5c7c253d96ed1b09550e56ec1a7")
    ZMIND_BASE_URL = os.getenv("ZMIND_BASE_URL", "https://zmind.whaletv.com")
    ZMIND_API_URL = ZMIND_BASE_URL  # 别名，保持兼容性
    # 支持多个项目标识符，用逗号分隔
    ZMIND_PROJECT_IDENTIFIERS = os.getenv("ZMIND_PROJECT_IDENTIFIERS", "okr-fz-rd-qa-fuzhou,whale-os-stb").split(",")

    # 反爬配置
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", "300"))
    RATE_LIMIT_LOGIN = int(os.getenv("RATE_LIMIT_LOGIN", "20"))
    CAPTCHA_ENABLED = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"
    CAPTCHA_FAIL_THRESHOLD = int(os.getenv("CAPTCHA_FAIL_THRESHOLD", "3"))
    REQUEST_SIGN_ENABLED = os.getenv("REQUEST_SIGN_ENABLED", "true").lower() == "true"
    REQUEST_SIGN_SECRET = os.getenv("REQUEST_SIGN_SECRET", "tms-sign-secret-2026")
    ANTI_BOT_ENABLED = os.getenv("ANTI_BOT_ENABLED", "true").lower() == "true"
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")  # 脚本API密钥，为空则禁用

settings = Settings()

# 导出常用配置
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
UPLOAD_DIR = settings.UPLOAD_DIR
ZMIND_API_KEY = settings.ZMIND_API_KEY
ZMIND_API_URL = settings.ZMIND_API_URL
ZMIND_BASE_URL = settings.ZMIND_BASE_URL
ZMIND_PROJECT_IDENTIFIERS = settings.ZMIND_PROJECT_IDENTIFIERS

