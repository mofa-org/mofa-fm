# 🎙️ MoFA FM - 播客托管平台

MoFA FM 是一个现代化的播客托管平台，采用 Django + Vue 3 技术栈，具有马卡龙配色的独特设计语言。

## ✨ 特性

- 🎨 **马卡龙设计系统** - 参考 voice-webapp 的独特视觉风格
- 🎵 **完整播客管理** - 创建节目、上传单集、播放器
- 👥 **创作者验证** - 数学题验证成为创作者
- 💬 **评论系统** - 嵌套评论支持
- 🔍 **全文搜索** - 搜索节目、单集和评论
- 📊 **播放历史** - 自动保存播放进度
- ❤️ **互动功能** - 点赞、关注、收藏

## 🏗️ 技术栈

### 后端
- **Django 5.1** - Web框架
- **Django REST Framework** - API
- **Celery** - 异步任务（音频处理）
- **Redis** - 缓存和消息队列
- **PostgreSQL/SQLite** - 数据库
- **pydub** - 音频处理

### 前端
- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Pinia** - 状态管理
- **Element Plus** - UI组件库
- **Axios** - HTTP客户端

## 📦 安装和运行

### 前置要求

- Python 3.10+
- Node.js 18+
- Redis (用于Celery)
- FFmpeg (用于音频处理)

### 后端设置

1. **创建虚拟环境并安装依赖**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，设置 SECRET_KEY 等配置
```

3. **初始化数据库**

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

4. **创建初始分类数据**

```python
python manage.py shell

from apps.podcasts.models import Category

categories = [
    {'name': '科技', 'slug': 'tech', 'icon': 'Monitor', 'color': '#ff513b'},
    {'name': '商业', 'slug': 'business', 'icon': 'Briefcase', 'color': '#ffc63e'},
    {'name': '文化', 'slug': 'culture', 'icon': 'Reading', 'color': '#6dcad0'},
    {'name': '教育', 'slug': 'education', 'icon': 'School', 'color': '#fd553f'},
    {'name': '娱乐', 'slug': 'entertainment', 'icon': 'Film', 'color': '#ff7b68'},
]

for cat in categories:
    Category.objects.create(**cat)
```

5. **启动开发服务器**

```bash
# 启动 Django
python manage.py runserver

# 新终端：启动 Redis
redis-server

# 新终端：启动 Celery Worker
celery -A config worker -l info

# 新终端：启动 Celery Beat (定时任务)
celery -A config beat -l info
```

### 前端设置

1. **安装依赖**

```bash
cd frontend
npm install
```

2. **启动开发服务器**

```bash
npm run dev
```

前端将在 http://localhost:5173 启动

### 访问应用

- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000/api
- **API文档**: http://localhost:8000/swagger
- **Django管理后台**: http://localhost:8000/admin

## 📁 项目结构

```
mofa-fm/
├── backend/                    # Django 后端
│   ├── config/                 # Django 配置
│   ├── apps/
│   │   ├── users/              # 用户系统
│   │   ├── podcasts/           # 播客核心
│   │   ├── interactions/       # 互动功能
│   │   └── search/             # 搜索
│   └── utils/                  # 工具类
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── assets/styles/      # 马卡龙设计系统
│   │   ├── components/         # 组件
│   │   ├── views/              # 页面
│   │   ├── stores/             # Pinia状态
│   │   ├── api/                # API客户端
│   │   └── router/             # 路由
│   └── package.json
│
└── media/                      # 媒体文件存储
```

## 🎨 马卡龙设计系统

设计系统包含：
- **色彩**: 红(#ff513b)、橙(#fd553f)、黄(#ffc63e)、青(#6dcad0)
- **几何风格**: 3px粗边框 + 偏移阴影
- **动画**: 平移式hover效果
- **渐变**: 顶部彩色渐变条

## 🚀 核心功能

### 用户系统
- 注册/登录
- 创作者验证（数学题）
- 用户资料管理

### 播客管理
- 创建播客节目
- 上传音频文件
- 自动音频处理（MP3转码、标准化）

### 播放器
- 全局底部播放器
- 进度保存
- 播放速度调整
- 音量控制
- 15秒快进/后退

### 互动功能
- 评论（嵌套回复）
- 点赞单集
- 关注节目
- 播放历史

### 搜索
- 全文搜索（标题 + 评论）
- 快速搜索（自动完成）

## 📝 API 端点

### 认证
- `POST /api/auth/register/` - 注册
- `POST /api/auth/login/` - 登录
- `GET /api/auth/me/` - 当前用户

### 播客
- `GET /api/podcasts/shows/` - 节目列表
- `GET /api/podcasts/shows/:slug/` - 节目详情
- `GET /api/podcasts/episodes/` - 单集列表
- `POST /api/podcasts/shows/create/` - 创建节目
- `POST /api/podcasts/episodes/create/` - 上传单集

### 互动
- `GET /api/interactions/episodes/:id/comments/` - 评论列表
- `POST /api/interactions/comments/create/` - 创建评论
- `POST /api/interactions/episodes/:id/like/` - 点赞
- `POST /api/interactions/shows/:id/follow/` - 关注
- `POST /api/interactions/play/update/` - 更新播放进度

### 搜索
- `GET /api/search/?q=keyword` - 全局搜索

## 🔧 开发提示

### 添加新的分类

```python
from apps.podcasts.models import Category
Category.objects.create(
    name='音乐',
    slug='music',
    icon='Headset',
    color='#6dcad0'
)
```

### 创建超级用户

```bash
python manage.py createsuperuser
```

### 运行测试

```bash
# 后端
python manage.py test

# 前端
npm run test
```

### 构建生产版本

```bash
# 后端
pip install -r requirements/prod.txt
python manage.py collectstatic

# 前端
npm run build
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Pull Request！

## 📧 联系

- Email: contact@mofa.ai
- Website: https://mofa.ai

---

**MoFA FM** - 让播客更精彩 🎵
