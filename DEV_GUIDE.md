# MoFA FM 本地开发指南

## 🚀 快速开始

### 一键启动所有服务

```bash
./dev-start.sh
```

启动内容：
- ✅ Redis（消息队列）
- ✅ Django 后端（端口 8000）
- ✅ Celery Worker（异步任务处理）
- ✅ 前端开发服务器（端口 5173）

启动后访问：
- 前端界面：http://localhost:5173
- 后端 API：http://localhost:8000/api
- 管理后台：http://localhost:8000/admin

---

### 停止所有服务

```bash
./dev-stop.sh
```

---

### 查看服务状态

```bash
./dev-status.sh
```

输出示例：
```
========================================
  MoFA FM 开发环境状态
========================================

  ✓ Redis: 运行中
  ✓ Django: 运行中 (PID: 12345)
    URL: http://localhost:8000
  ✓ Celery: 运行中 (PID: 12346)
  ✓ 前端: 运行中 (PID: 12347)
    URL: http://localhost:5173
```

---

### 查看日志

查看单个服务日志：
```bash
./dev-logs.sh django    # Django 日志
./dev-logs.sh celery    # Celery 日志
./dev-logs.sh frontend  # 前端日志
```

查看所有日志：
```bash
./dev-logs.sh all
```

日志文件位置：
- Django: `.dev-pids/django.log`
- Celery: `.dev-pids/celery.log`
- 前端: `.dev-pids/frontend.log`

---

## 🔧 首次使用前的准备

### 1. 安装依赖

**后端依赖**：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
```

**前端依赖**：
```bash
cd frontend
npm install
```

**Redis**（如果本地没有）：
```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt install redis-server

# Windows (WSL)
sudo apt install redis-server
```

---

### 2. 配置环境变量

复制示例配置文件：
```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，配置必要的 API keys：
```bash
# 必须配置（用于 AI 功能）
OPENAI_API_KEY=你的moonshot-api-key
MINIMAX_API_KEY=你的minimax-api-key

# 可选（用于 AI 搜索）
TAVILY_API_KEY=你的tavily-api-key
```

**提示**：如果只是前端开发，可以跳过 API keys 配置。

---

### 3. 数据库迁移

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser  # 创建管理员账号
```

---

## 📝 开发工作流

### 场景 1：只改前端（最常见）

```bash
./dev-start.sh
# 访问 http://localhost:5173
# 修改 frontend/ 下的文件，自动热重载
```

---

### 场景 2：改后端代码

```bash
./dev-start.sh
# 修改 backend/ 下的 Python 文件
# Django 会自动重启（无需手动操作）
```

---

### 场景 3：测试 AI 功能

确保 `.env` 中配置了 API keys，然后：
```bash
./dev-start.sh
# Celery Worker 会自动处理 AI 任务
# 查看 Celery 日志：./dev-logs.sh celery
```

---

## 🐛 故障排查

### 端口被占用

如果提示端口被占用：
```bash
# 查看占用端口的进程
lsof -i :8000   # Django
lsof -i :5173   # 前端

# 杀掉进程
kill -9 <PID>
```

---

### Redis 连接失败

检查 Redis 是否运行：
```bash
redis-cli ping
# 应该返回 PONG
```

启动 Redis：
```bash
redis-server --daemonize yes
```

---

### 前端无法访问后端 API

检查 CORS 配置：
- 确保 `backend/.env` 中 `CORS_ALLOWED_ORIGINS` 包含 `http://localhost:5173`
- 默认配置已包含，无需修改

---

### Celery 任务不执行

1. 检查 Celery Worker 是否运行：
   ```bash
   ./dev-status.sh
   ```

2. 查看 Celery 日志：
   ```bash
   ./dev-logs.sh celery
   ```

3. 检查 `.env` 中的 API keys 是否配置正确

---

## 💡 进阶技巧

### 只启动部分服务

如果你只需要前端 + 后端（不需要 AI 功能），可以手动启动：

```bash
# 终端 1：启动后端
cd backend
source venv/bin/activate
python manage.py runserver

# 终端 2：启动前端
cd frontend
npm run dev
```

这样就不需要 Redis 和 Celery Worker 了。

---

### 连接测试服务器的数据库

如果想使用测试服务器的数据，可以配置 SSH 隧道：

```bash
# 转发测试服务器的 Redis
ssh -L 6379:localhost:6379 root@test.mofa.fm

# 现在本地的 Redis 连接会转发到测试服务器
```

---

## 📚 相关文档

- [后端 API 文档](http://localhost:8000/swagger/)
- [项目架构文档](architecture.md)
- [AI 功能实现](AI_SCRIPT_IMPLEMENTATION_SUMMARY.md)

---

## ❓ 常见问题

**Q: 启动脚本在 Windows 上能用吗？**
A: 这些是 Bash 脚本，需要在 WSL（Windows Subsystem for Linux）或 Git Bash 中运行。

**Q: 能在服务器上用这些脚本吗？**
A: 不建议。服务器用 systemd 管理服务更稳定，这些脚本仅用于本地开发。

**Q: 如何重启某个服务？**
A: 先 `./dev-stop.sh` 停止所有服务，再 `./dev-start.sh` 启动。或者手动 kill 对应 PID 后重新启动。

---

**祝开发愉快！🎉**
