# MoFA FM - 播客托管平台

MoFA FM 是一个现代化的播客托管和分发平台，支持播客创作、AI 脚本生成、语音合成以及完整的社区互动功能。

## 主要功能

- 播客节目和单集管理
- AI 辅助脚本创作
- TTS 语音合成
- 用户社区互动（评论、点赞、关注）
- 全文搜索
- 播放历史和进度保存
- 创作者管理系统

## 技术栈

### 后端
- Django 5.1
- Django REST Framework
- Celery (异步任务)
- Redis (缓存和消息队列)
- PostgreSQL/SQLite

### 前端
- Vue 3
- Vite
- Pinia (状态管理)
- Element Plus (UI组件)

### AI 服务
- Moonshot AI (脚本生成)
- MiniMax (TTS语音合成)
- Tavily (AI搜索)

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Redis
- FFmpeg

### 后端部署

1. 创建虚拟环境并安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/prod.txt
```

2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# Django
DEBUG=False
ALLOWED_HOSTS=your-domain.com
SECRET_KEY=your-secret-key
CSRF_TRUSTED_ORIGINS=https://your-domain.com

# AI Services
OPENAI_API_KEY=your-moonshot-api-key
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=moonshot-v1-8k

MINIMAX_API_KEY=your-minimax-api-key
TAVILY_API_KEY=your-tavily-api-key
```

3. 初始化数据库

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4. 创建管理员账号

```bash
python manage.py createsuperuser
```

5. 启动服务

```bash
# 使用 gunicorn 启动 Django
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# 启动 Celery Worker
celery -A config worker -l info

# 启动 Celery Beat
celery -A config beat -l info
```

### 前端部署

1. 安装依赖并构建

```bash
cd frontend
npm install
npm run build
```

2. 配置 Nginx

将构建后的文件部署到 `/var/www/your-domain`，配置 Nginx 反向代理：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/your-domain;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Static files
    location /static/ {
        alias /path/to/backend/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /path/to/media/;
    }
}
```

## 使用指南

### 访问管理后台

管理后台地址：`https://your-domain.com/admin/`

默认管理员账号：
- 用户名：admin
- 密码：mofamofa

管理后台可以管理：
- 用户和创作者
- 播客节目和单集
- 分类和标签
- 评论和互动
- 搜索记录

### 查看系统状态

系统状态页面：`https://your-domain.com/status`

实时监控以下服务：
- API 服务状态
- 数据库连接
- Redis 缓存
- AI 脚本生成服务
- TTS 语音合成服务
- 搜索服务

### API 文档

- Swagger 文档：`https://your-domain.com/swagger/`
- ReDoc 文档：`https://your-domain.com/redoc/`

## 项目结构

```
mofa-fm/
├── backend/                # Django 后端
│   ├── apps/
│   │   ├── users/          # 用户系统
│   │   ├── podcasts/       # 播客管理
│   │   ├── interactions/   # 社区互动
│   │   ├── search/         # 搜索功能
│   │   └── core/           # 核心功能
│   ├── config/             # Django 配置
│   └── utils/              # 工具类
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # 状态管理
│   │   ├── api/            # API 客户端
│   │   └── router/         # 路由配置
│   └── package.json
│
└── media/                  # 媒体文件存储
```

## 开发模式

### 后端开发

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

### 前端开发

```bash
cd frontend
npm run dev
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api
- API 文档：http://localhost:8000/swagger

## 生产环境优化

1. 使用 PostgreSQL 替代 SQLite
2. 配置 Redis 持久化
3. 启用 Nginx 缓存
4. 配置 SSL 证书
5. 设置 Celery 进程监控
6. 配置日志收集和监控

## 维护指南

### 备份数据

```bash
# 备份数据库
python manage.py dumpdata > backup.json

# 备份媒体文件
tar -czf media-backup.tar.gz media/
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements/prod.txt
python manage.py migrate
python manage.py collectstatic --noinput

# 重启服务
systemctl restart your-app-service

# 更新前端
cd frontend
npm install
npm run build
```

## 许可证

MIT License

## 联系方式

- Website: https://mofa.fm
- Email: contact@mofa.ai

## 技术支持

详细技术文档请参考 `README.bak.md`
