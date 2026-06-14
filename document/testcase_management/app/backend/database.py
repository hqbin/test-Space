from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# 根据数据库类型设置不同的参数
if settings.DATABASE_URL.startswith('sqlite'):
    # SQLite配置
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL或其他数据库配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # 连接池预检查
        pool_size=20,  # 连接池大小（从10增加到20）
        max_overflow=40,  # 最大溢出连接数（从20增加到40）
        pool_recycle=3600,  # 连接回收时间（1小时）
        echo=False  # 生产环境关闭SQL日志
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
