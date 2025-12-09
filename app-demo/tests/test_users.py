import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 在导入应用前设置默认测试数据库，避免连接到真实 Postgres
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def override_session(tmp_path) -> Generator[sessionmaker, None, None]:
    """为每个测试创建独立的 SQLite 底库并清理干净。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, future=True
    )

    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(override_session) -> Generator[TestClient, None, None]:
    def _override_get_db():
        db = override_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_user_success(client: TestClient):
    payload = {"username": "alice", "password": "secret123"}

    response = client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert "id" in data and data["id"] > 0
    assert "created_at" in data


def test_duplicate_username_returns_400(client: TestClient):
    payload = {"username": "bob", "password": "strongpass"}

    first = client.post("/users", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/users", json=payload)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Username already registered"


def test_list_users_orders_by_id(client: TestClient):
    users = [
        {"username": "charlie", "password": "pass1234"},
        {"username": "diana", "password": "pass5678"},
    ]

    for user in users:
        assert client.post("/users", json=user).status_code == 201

    response = client.get("/users")
    assert response.status_code == 200

    body = response.json()
    assert [item["username"] for item in body] == [u["username"] for u in users]
    ids = [item["id"] for item in body]
    assert ids == sorted(ids)
