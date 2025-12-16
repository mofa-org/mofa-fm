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

## 部署说明（当前线上环境）

- 代码与数据路径：`/mnt/data/mofa-fm`，媒体 `/mnt/data/mofa-fm/media`，静态 `/mnt/data/mofa-fm/backend/staticfiles`，虚拟环境 `/mnt/data/mofa-fm/backend/venv`。
- 依赖：Python 3.12，Node 18，Redis（apt 安装，127.0.0.1:6379），FFmpeg。
- 数据库：默认 SQLite `/mnt/data/mofa-fm/backend/db.sqlite3`，可改为 PostgreSQL（改 `.env` 的 `DATABASE_URL`）。
- 服务：Gunicorn 127.0.0.1:8000、Celery worker、Celery beat、Nginx（反代前后端，TLS via Certbot）。
- 热搜接口：`TRENDING_API_URL` 默认 `http://154.21.90.242:1145`。

### 环境变量

根目录 `.env` 示例（已部署：DJANGO_ENV=prod，HOST/CSRF/CORS 指向 `mofa.fm`）：
```
DJANGO_ENV=prod
ALLOWED_HOSTS=mofa.fm,18.166.66.71,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://mofa.fm,http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOWED_ORIGINS=https://mofa.fm,http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:////mnt/data/mofa-fm/backend/db.sqlite3
REDIS_URL=redis://localhost:6379/0
MEDIA_ROOT=/mnt/data/mofa-fm/media
STATIC_ROOT=/mnt/data/mofa-fm/backend/staticfiles
TRENDING_API_URL=http://154.21.90.242:1145
OPENAI_API_KEY=...
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=moonshot-v1-8k
MINIMAX_API_KEY=...
TAVILY_API_KEY=...
```

### 一键更新脚本（推荐）

`sudo update-fm`  
流程：git pull main（使用 ubuntu 用户 SSH key）→ 后端依赖 → migrate → collectstatic → 前端 `npm ci && npm run build` → 重启 `mofa-fm-gunicorn`、`mofa-fm-celery`、`mofa-fm-celery-beat`、`nginx`。  
日志：`/mnt/data/mofa-fm/backend/logs/update-YYYYMMDD_HHMMSS.log`

### 手动部署要点

1) 后端依赖  
```
cd /mnt/data/mofa-fm/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

2) 前端构建  
```
cd /mnt/data/mofa-fm/frontend
npm ci
npm run build
```

3) 服务与端口  
- Gunicorn: 127.0.0.1:8000  
- Celery worker/beat: 依赖 Redis  
- Nginx: 443/80，前端根 `/mnt/data/mofa-fm/frontend/dist`，`/api`/`/admin` 反代 127.0.0.1:8000，静态 `/mnt/data/mofa-fm/backend/staticfiles`，媒体 `/mnt/data/mofa-fm/media`  
- systemd：`mofa-fm-gunicorn`、`mofa-fm-celery`、`mofa-fm-celery-beat`

4) HTTPS  
Certbot 证书路径：`/etc/letsencrypt/live/mofa.fm/`，已自动续期。

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
