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
        # 存储后端随 .env 配置：V1=memory，V2 配好 MySQL 后=mysql
        assert body["data"]["storage"] in {"memory", "mysql"}
        assert "asr" in body["data"]


def test_meeting_list_shape() -> None:
    """列表接口结构正确即可，不假设数据库为空（V2 启用 MySQL 后可能有历史数据）。"""
    with TestClient(app) as client:
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data["total"], int) and data["total"] >= 0
        assert isinstance(data["items"], list)
        assert "page" in data and "page_size" in data


def test_not_found_meeting() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/meetings/does-not-exist")
        assert resp.status_code == 404
        assert resp.json()["code"] == 40401
