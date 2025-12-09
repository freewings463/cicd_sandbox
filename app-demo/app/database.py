import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# 允许通过 DATABASE_URL 覆盖默认的 Postgres 连接，便于在 CI/单元测试中使用 SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "appuser")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "apppassword")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "appdb")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# SQLite 需要额外的 connect_args 以允许多线程（FastAPI TestClient 会跨线程调用）
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
