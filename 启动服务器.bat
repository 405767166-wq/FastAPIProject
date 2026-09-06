@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   会议纪要转写系统 backend 启动中...
echo   停止请按 Ctrl+C
echo   接口文档: http://127.0.0.1:8000/docs
echo ============================================
.\.venv\Scripts\python.exe backend\run.py
echo.
echo 服务已退出（若未启动成功请把上方报错发给我）
pause
