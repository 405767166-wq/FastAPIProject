"""P2.1 上传接口单元测试：合法文件返回 meeting_id，非音频返回 400 + 40001。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_upload_valid_audio_returns_meeting_id() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/api/meetings",
            files={"file": ("meeting.mp3", b"fake-audio-content", "audio/mpeg")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["meeting_id"]
    assert body["data"]["status"] == "queued"
    assert body["data"]["progress"] == 0
    assert body["data"]["message"]


@pytest.mark.parametrize("ext", ["mp3", "wav", "m4a", "aac"])
def test_upload_accepts_all_audio_extensions(ext: str) -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/api/meetings",
            files={"file": (f"recording.{ext}", b"audio", "application/octet-stream")},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["meeting_id"]


def test_upload_with_title() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/api/meetings",
            files={"file": ("meeting.wav", b"audio", "audio/wav")},
            data={"title": "周会录音"},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "周会录音"


def test_upload_non_audio_returns_400_param() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/api/meetings",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 400
    assert resp.json()["code"] == 40001


def test_upload_without_file_returns_422() -> None:
    """缺少必填 file 字段时由 FastAPI 默认校验拦截（原骨架阶段返回 501）。"""
    with TestClient(app) as client:
        resp = client.post("/api/meetings")
    assert resp.status_code == 422
