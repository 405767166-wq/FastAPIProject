"""REST API 聚合路由（M3）。V1 阶段：health + meetings。"""

from fastapi import APIRouter

from app.api import health, meetings

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(meetings.router, tags=["meetings"])
