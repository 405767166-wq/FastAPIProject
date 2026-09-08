# nginx — 反向代理网关（V2）

本目录是**自包含**的 Windows 版 Nginx（已内置 `nginx.exe`），负责：

| 路径 | 作用 |
|------|------|
| `/` | 托管 Vue3 前端构建产物 `frontend/dist`（SPA 路由回退） |
| `/api/*` | 反向代理到后端 FastAPI `http://127.0.0.1:8000`（保留前缀） |
| `/ws` | WebSocket 反代（V2 实时进度，Upgrade 透传） |

## 目录结构

```
nginx/
├─ nginx.exe          # 启动程序
├─ conf/nginx.conf    # 本项目的反向代理配置
├─ conf/mime.types    # 静态文件类型
├─ logs/              # 运行日志（运行期生成）
├─ temp/              # 临时文件
└─ html/              # 默认站点（本项目不使用）
```

## 启动顺序（三个都起）

```powershell
# ① 后端
.\.venv\Scripts\python.exe backend\run.py        # 或双击 启动服务器.bat，端口 8000

# ② 前端构建（改过前端源码后重新 build）
cd frontend; npm run build; cd ..

# ③ Nginx（-p 指定本目录为 prefix）
.\nginx\nginx.exe -p .\nginx\
```

然后浏览器访问 **http://127.0.0.1:8080**（不要直接访问 8000/5173）。

## 常用命令

```powershell
# 启动 / 停止 / 重载配置 / 查进程
.\nginx\nginx.exe -p .\nginx\
.\nginx\nginx.exe -p .\nginx\ -s stop
.\nginx\nginx.exe -p .\nginx\ -s quit
.\nginx\nginx.exe -p .\nginx\ -s reload
.\nginx\nginx.exe -p .\nginx\ -t                    # 测试配置语法
```

## 前端开发模式（热更新）

开发时不想每次 build，可让 Nginx 把 `/` 反代到 Vite dev server：

1. 另开终端：`cd frontend; npm run dev`（端口 5173）
2. 打开 `nginx/conf/nginx.conf`，把 `location /` 改成注释里"开发模式"那段（`proxy_pass http://127.0.0.1:5173`）
3. `nginx.exe -s reload`

## 端口约定

| 端口 | 用途 |
|------|------|
| 8080 | Nginx 入口（前端 + 反代后端） |
| 8000 | FastAPI 后端 |
| 5173 | Vite dev server（仅开发模式） |
