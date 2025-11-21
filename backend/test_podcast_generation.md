# 播客生成功能测试指南

## 已完成的功能模块 ✅

### 1. AI 脚本生成系统
- **模型**: `ScriptSession`, `UploadedReference`
- **服务**: `script_ai.py` (Kimi API)
- **文件解析**: `file_parser.py` (支持 txt/pdf/md/docx)

### 2. MiniMax TTS 集成
- **客户端**: `minimax_client.py` (WebSocket 流式 TTS)
- **配置**: `MiniMaxVoiceConfig` 数据类
- **音色**: 支持自定义音色配置

### 3. 播客音频生成
- **生成器**: `generator.py` (PodcastGenerator 类)
- **脚本解析**: 支持 markdown 格式 【角色名】
- **音频合成**: 自动拼接 + 说话人切换静音

### 4. Celery 任务
- **任务**: `generate_podcast_task`
- **状态管理**: draft → processing → published/failed

## API 端点

### ScriptSession ViewSet (`/api/v1/podcasts/script-sessions/`)

**1. 创建会话**
```bash
POST /api/v1/podcasts/script-sessions/
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "测试播客脚本",
  "show_id": 1  // 可选
}
```

**2. 上传参考文件**
```bash
POST /api/v1/podcasts/script-sessions/{id}/upload_file/
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: [选择文件: .txt/.pdf/.md/.docx]
```

**3. 与 AI 对话**
```bash
POST /api/v1/podcasts/script-sessions/{id}/chat/
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "帮我生成一个关于人工智能的播客脚本，要有两个主持人对话"
}
```

**响应示例**:
```json
{
  "success": true,
  "response": "好的，我来帮你创建一个关于人工智能的播客脚本...\n\n```markdown\n【大牛】大家好！欢迎来到本期节目...\n【一帆】今天我们要聊聊人工智能...\n```",
  "script": "【大牛】大家好！欢迎来到本期节目...\n【一帆】今天我们要聊聊人工智能...",
  "script_updated": true,
  "session": {
    "id": 1,
    "title": "测试播客脚本",
    "current_script": "【大牛】大家好...",
    "chat_history": [...]
  }
}
```

**4. 生成音频**
```bash
POST /api/v1/podcasts/episodes/generate/
Content-Type: application/json
Authorization: Bearer <token>

{
  "show_id": 1,
  "title": "第一期：人工智能简介",
  "description": "介绍人工智能的基础知识",
  "script_content": "【大牛】大家好！\n【一帆】欢迎收听..."
}
```

## 测试流程

### 准备工作
1. 确保 Redis 已启动（Celery 依赖）
```bash
redis-server
```

2. 启动 Celery Worker
```bash
cd backend
celery -A config worker -l info
```

3. 运行 Django 开发服务器
```bash
cd backend
python manage.py runserver
```

### 完整测试步骤

**步骤 1: 创建用户和节目**
- 注册/登录获取 JWT token
- 创建一个播客节目

**步骤 2: 创建脚本会话**
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/script-sessions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI 播客测试",
    "show_id": 1
  }'
```

**步骤 3: （可选）上传参考文件**
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/script-sessions/1/upload_file/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/reference.txt"
```

**步骤 4: 与 AI 对话生成脚本**
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/script-sessions/1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我生成一个3分钟的播客脚本，主题是Python编程入门，要有两个主持人对话，一个叫大牛，一个叫一帆"
  }'
```

**步骤 5: 继续对话优化脚本（可多次）**
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/script-sessions/1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "可以让对话更幽默一点吗？增加一些编程段子"
  }'
```

**步骤 6: 生成音频**
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/episodes/generate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": 1,
    "title": "Python编程入门",
    "description": "适合新手的Python入门讲解",
    "script_content": "【大牛】大家好...\n【一帆】欢迎收听..."
  }'
```

**步骤 7: 检查生成状态**
- 查看 Celery Worker 日志
- 检查 Episode 的 status 字段：`processing` → `published`
- 下载生成的 MP3 文件

## 脚本格式规范

### 支持的格式
```markdown
# 标题（可选）

【大牛】这是大牛说的话。

【一帆】这是一帆说的话。

【大牛】可以继续说，
支持多行文本。

## 章节（可选）

【大牛】可以在脚本中使用 markdown 格式。
```

### 角色别名（可配置）
- `【大牛】` → `daniu` → `voice_id: ttv-voice-2025103011222725-sg8dZxUP`
- `【一帆】` → `yifan` → `voice_id: moss_audio_aaa1346a-7ce7-11f0-8e61-2e6e3c7ee85d`

### 添加自定义音色
在 `backend/config/settings/base.py` 中配置：
```python
MINIMAX_TTS = {
    # ... 其他配置 ...
    'voices': {
        'custom_voice': {
            'voice_id': 'your-minimax-voice-id',
            'speed': 1.0,
            'volume': 1.0,
            'pitch': 0,
        }
    },
    'aliases': {
        '小明': 'custom_voice',
    }
}
```

然后在脚本中使用：
```markdown
【小明】我是用自定义音色的主持人。
```

## 配置检查清单

### 环境变量 (.env)
```bash
# Kimi AI (脚本生成)
KIMI_API_KEY=sk-fady32pXoL8vhKMKQhuyGXfsPaboF5JGO80ScDa6MUnHV9OT

# MiniMax TTS (语音合成)
MINIMAX_API_KEY=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

# 可选的 MiniMax 配置
MINIMAX_MODEL=speech-2.5-hd-preview
MINIMAX_SAMPLE_RATE=32000
MINIMAX_MAX_SEGMENT_CHARS=120
MINIMAX_SILENCE_MIN_MS=300
MINIMAX_SILENCE_MAX_MS=1200
```

### 依赖包
```bash
pip install -r requirements/base.txt
```

关键依赖：
- `openai>=1.0.0` - Kimi API
- `websockets>=11.0.3` - MiniMax WebSocket
- `PyPDF2>=3.0.0` - PDF 解析
- `python-docx>=1.1.0` - Word 文档解析
- `pydub==0.25.1` - 音频处理

### 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

## 已知限制和注意事项

### 1. 文本长度限制
- MiniMax 单次请求最大 120 字（可配置）
- 自动分段处理，优先在标点符号处切分

### 2. 音色数量
- 默认提供 2 个音色（大牛、一帆）
- 可通过配置添加更多音色

### 3. 并发处理
- Celery 任务异步执行
- 大量生成请求需要配置足够的 Worker

### 4. 文件大小
- 上传文件最大 10MB（可调整）
- PDF 和 Word 文件提取纯文本

### 5. API 配额
- Kimi API 和 MiniMax API 都有请求限制
- 生产环境需要监控配额使用情况

## 故障排查

### 问题 1: Celery 任务失败
**检查**:
- Redis 是否运行
- Celery Worker 日志
- API Key 是否正确配置

### 问题 2: MiniMax 连接失败
**检查**:
- MINIMAX_API_KEY 是否有效
- 网络是否可以访问 `wss://api.minimax.io`
- SSL 证书问题（代码已禁用证书验证）

### 问题 3: 脚本解析失败
**检查**:
- 脚本是否使用 【角色名】 格式
- 角色名是否在配置的别名中
- 是否有空白内容

### 问题 4: AI 响应错误
**检查**:
- KIMI_API_KEY 是否有效
- 请求是否超过 token 限制（moonshot-v1-8k: 8000 tokens）
- 对话历史是否过长

## 下一步开发建议

### 前端集成
1. 创建 ScriptSession 管理界面
2. 实现聊天界面（类似 ChatGPT）
3. 显示脚本版本历史
4. 音频播放器集成

### 功能增强
1. 脚本模板库
2. 批量生成播客
3. 音频后期处理（背景音乐、音效）
4. 多语言支持

### 性能优化
1. 缓存 AI 响应
2. 预加载常用音色
3. 分布式任务队列
4. CDN 集成

## 测试完成标志

- [x] 后端 API 全部实现
- [x] Kimi AI 脚本生成
- [x] MiniMax TTS 集成
- [x] 文件上传和解析
- [x] Celery 异步任务
- [x] 数据库模型和迁移
- [x] 错误处理和日志
- [ ] 前端界面（待实现）
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 部署配置
