# AI 脚本创作功能使用文档

## 功能概述

AI 脚本创作功能允许创作者通过与 AI 对话的方式，生成播客脚本。支持：
- 📝 多轮对话生成和修改脚本
- 📎 上传参考文件 (txt, pdf, md, docx)
- 💾 自动保存对话历史和脚本版本
- 🎙️ 音频生成（占位，待实现）

## API 端点

### 1. 创建脚本会话

```http
POST /api/podcasts/script-sessions/
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "我的播客脚本",
  "show_id": 1  // 可选，关联的节目ID
}
```

**响应:**
```json
{
  "id": 1,
  "title": "我的播客脚本",
  "status": "active",
  "creator": {...},
  "show": {...},
  "chat_history": [],
  "current_script": "",
  "script_versions": [],
  "voice_config": {},
  "uploaded_files": [],
  "uploaded_files_count": 0,
  "created_at": "2025-11-20T...",
  "updated_at": "2025-11-20T..."
}
```

### 2. 获取会话列表

```http
GET /api/podcasts/script-sessions/
Authorization: Bearer {token}
```

### 3. 获取单个会话详情

```http
GET /api/podcasts/script-sessions/{id}/
Authorization: Bearer {token}
```

### 4. 与 AI 对话

```http
POST /api/podcasts/script-sessions/{id}/chat/
Content-Type: application/json
Authorization: Bearer {token}

{
  "message": "帮我创建一个关于AI技术的播客脚本，5分钟，两个人对话"
}
```

**响应:**
```json
{
  "message": "好的，我来帮你创作...\n\n```markdown\n【主持人】欢迎...",
  "script": "【主持人】欢迎来到今天的节目...\n【嘉宾】很高兴来到这里...",
  "has_script_update": true
}
```

### 5. 上传参考文件

```http
POST /api/podcasts/script-sessions/{id}/upload_file/
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: <文件>
```

**支持的文件类型:**
- `.txt` - 文本文件
- `.pdf` - PDF 文档
- `.md` - Markdown 文档
- `.docx` - Word 文档

**响应:**
```json
{
  "id": 1,
  "original_filename": "参考资料.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "file_url": "http://localhost:8000/media/script_references/2025/11/...",
  "extracted_text": "这是从PDF中提取的文本...",
  "uploaded_at": "2025-11-20T..."
}
```

### 6. 生成音频（占位）

```http
POST /api/podcasts/script-sessions/{id}/generate_audio/
Authorization: Bearer {token}
```

**响应:**
```json
{
  "message": "音频生成功能即将上线",
  "script": "...",
  "status": "pending"
}
```

### 7. 更新会话

```http
PATCH /api/podcasts/script-sessions/{id}/
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "新标题",
  "status": "completed"  // active, completed, archived
}
```

### 8. 删除会话

```http
DELETE /api/podcasts/script-sessions/{id}/
Authorization: Bearer {token}
```

## 使用流程示例

### 1. 创建会话
```bash
curl -X POST http://localhost:8000/api/podcasts/script-sessions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "AI播客脚本"}'
```

### 2. 上传参考资料
```bash
curl -X POST http://localhost:8000/api/podcasts/script-sessions/1/upload_file/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/reference.pdf"
```

### 3. 与AI对话生成脚本
```bash
curl -X POST http://localhost:8000/api/podcasts/script-sessions/1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "基于上传的资料，帮我生成一个5分钟的播客脚本"}'
```

### 4. 修改脚本
```bash
curl -X POST http://localhost:8000/api/podcasts/script-sessions/1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "把开场白改短一点"}'
```

### 5. 查看脚本历史版本
```bash
curl http://localhost:8000/api/podcasts/script-sessions/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 脚本格式说明

AI 生成的脚本使用 Markdown 格式，角色标签格式为 `【角色名】`：

```markdown
# 播客标题

【主持人】大家好，欢迎来到今天的节目。我是主持人。

【嘉宾】大家好，我是嘉宾。今天我们聊聊人工智能。

【主持人】没错，最近AI技术发展很快...
```

**特点:**
- 角色名可以自定义（如"主持人"、"嘉宾A"、"专家李老师"等）
- 支持任意数量的角色
- AI 会自动保证对话的自然流畅性

## 数据模型

### ScriptSession
```python
{
  "id": int,
  "title": str,
  "status": str,  // active, completed, archived
  "creator": User,
  "show": Show,  // 可选
  "chat_history": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "current_script": str,  // Markdown格式
  "script_versions": [
    {"version": 1, "script": "...", "timestamp": "..."}
  ],
  "voice_config": {},  // 音色配置（待实现）
  "created_at": datetime,
  "updated_at": datetime
}
```

### UploadedReference
```python
{
  "id": int,
  "session": ScriptSession,
  "file": FileField,
  "original_filename": str,
  "file_type": str,  // txt, pdf, md, docx
  "file_size": int,
  "extracted_text": str,
  "uploaded_at": datetime
}
```

## 配置项

在 `.env` 文件中添加：

```env
# AI功能 (Kimi API)
KIMI_API_KEY=your-kimi-api-key-here
```

## 错误处理

### 常见错误

**1. API Key 未配置**
```json
{
  "error": "AI调用失败: KIMI_API_KEY 未配置"
}
```
解决方法：在 `.env` 中添加 `KIMI_API_KEY`

**2. 文件类型不支持**
```json
{
  "error": "不支持的文件类型: exe"
}
```
解决方法：只上传 txt, pdf, md, docx 格式文件

**3. 文件解析失败**
```json
{
  "error": "文件解析失败: 无法读取PDF"
}
```
解决方法：确保文件格式正确且未损坏

## 前端集成建议

### Vue 组件结构
```
views/creator/
└── ScriptChat.vue          # 主界面
    ├── ChatPanel           # 对话面板
    ├── FileUploader        # 文件上传
    └── ScriptPreview       # 脚本预览
```

### API 调用示例 (JavaScript)
```javascript
// 创建会话
const createSession = async () => {
  const response = await axios.post('/api/podcasts/script-sessions/', {
    title: '我的播客脚本'
  });
  return response.data;
};

// 发送消息
const sendMessage = async (sessionId, message) => {
  const response = await axios.post(
    `/api/podcasts/script-sessions/${sessionId}/chat/`,
    { message }
  );
  return response.data;
};

// 上传文件
const uploadFile = async (sessionId, file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(
    `/api/podcasts/script-sessions/${sessionId}/upload_file/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};
```

## 注意事项

1. **API 调用频率**: Kimi API 有频率限制，建议添加节流机制
2. **文件大小**: 建议限制上传文件不超过 10MB
3. **对话历史**: 会话会保存完整对话历史，长期使用可能导致数据量较大
4. **脚本版本**: 每次修改都会保存历史版本，方便回溯
5. **权限控制**: 只有创作者可以访问自己的会话

## 待实现功能

- [ ] 音频生成功能
- [ ] 音色选择和配置
- [ ] 脚本导出（PDF、Word）
- [ ] 批量会话管理
- [ ] 协作编辑
