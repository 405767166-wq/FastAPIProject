"""骨架冒烟测试：应用可启动、健康检查与基础路由工作。"""

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "up"
        assert body["data"]["storage"] == "memory"
        assert body["data"]["asr"] == "mock"


def test_empty_meeting_list() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []


def test_not_found_meeting() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/meetings/does-not-exist")
        assert resp.status_code == 404
        assert resp.json()["code"] == 40401
