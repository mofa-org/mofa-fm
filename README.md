# MoFA Voice WebApp

AI 驱动的播客生成平台 - 通过多轮对话创建高质量播客音频

## 🎯 功能特性

- **AI 对话生成脚本**：与 AI 多轮交互，智能生成播客脚本
- **脚本管理**：支持手动上传或 AI 生成脚本
- **音频生成**：选择声音配置，生成 WAV/MP3 格式音频
- **任务队列**：异步处理音频生成任务，支持进度查询
- **Credit 系统**：完整的计费和交易记录

## 📁 项目结构

```
voice-webapp/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 接口
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic Schemas
│   │   ├── core/        # 核心配置
│   │   └── main.py      # 应用入口
│   ├── requirements.txt
│   └── run.py           # 启动脚本
│
├── frontend/            # Vue3 前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── router/      # 路由配置
│   │   ├── store/       # Pinia 状态管理
│   │   └── api/         # API 调用
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    └── design.md        # 设计文档
```

## 🚀 快速开始

### 1. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py

# 访问 API 文档
open http://localhost:8000/api/docs
```

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问应用
open http://localhost:3000
```

## 📝 当前状态

### ✅ 已完成

- 完整的前后端框架搭建
- 7 张数据库表设计（Users, Scripts, Conversations, Tasks, Audios, etc.）
- 所有 API 接口（返回 Mock 数据）
- 完整的前端页面：
  - 登录/注册
  - AI 对话（多轮交互）
  - 脚本列表和上传
  - 任务管理和音频下载
  - Credit 管理

### 🔨 待实现（真实功能）

- [ ] 数据库迁移脚本（Alembic）
- [ ] JWT 认证逻辑
- [ ] AI 对话集成（OpenAI/Claude API）
- [ ] 音频生成引擎（DirectEngine）
- [ ] Redis 任务队列
- [ ] Credit 扣费事务

## 🎨 技术栈

### 后端
- FastAPI 0.109
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- Pydantic

### 前端
- Vue 3.4
- Element Plus 2.5
- Vue Router 4.2
- Pinia 2.1
- Axios

## 📦 Mock 数据说明

当前所有接口返回 Mock 数据，用于前端开发和演示：

- **LLM 回复**：返回 "xxxxx xxxxx xxxxx"
- **播客脚本**：返回格式正确的占位符 "【大牛】xxxxx\n\n【一帆】xxxxx"
- **音频文件**：生成不同频率的正弦波（440Hz 和 554Hz）

## 🔐 默认账号

- 用户名：demo_user
- 邮箱：demo@example.com
- 密码：任意（Mock 模式下无验证）
- 初始 Credit：1000

## 📖 API 文档

启动后端后访问：http://localhost:8000/api/docs

主要接口：
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/conversations` - 创建对话
- `POST /api/conversations/{id}/messages` - 发送消息
- `POST /api/scripts` - 上传脚本
- `POST /api/tasks` - 创建音频任务
- `GET /api/tasks/{id}` - 查询任务状态

## 🎯 下一步

1. **集成真实 LLM**：实现 OpenAI/Claude API 调用
2. **实现音频生成**：基于 MiniMax SDK 的 DirectEngine
3. **数据库持久化**：运行 Alembic 迁移，连接 PostgreSQL
4. **异步任务**：Redis 队列 + Worker 进程

## 📄 License

Part of the MoFA project
