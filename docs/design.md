  1. 框架

  后端：FastAPI + MoFA + Redis
  前端：Vue3 + ElementPlus

  2. 数据流可替换设计

  核心：定义通用接口，MoFA和直连TTS都实现这个接口

  • 接口规范：输入（脚本+声音A+声音B），输出（任务ID+状态+音频地址）
  • MoFA实现：现在用，功能全但较重
  • 直连实现：预留，轻量快速，性能瓶颈时启用
  • 切换方式：配置文件改引擎类型，业务代码不动

  解耦方式：MoFA独立进程，通过Redis队列通信，状态存Redis，换实现/升级数据流只要接口一致

  3. 数据库设计（PostgreSQL）

  核心表结构（5表模型）：

  User 表 - 用户账户
  • id (UUID PK), username, email, password_hash
  • credit_balance (剩余credit), total_credit_purchased (累计充值)
  • status (active/suspended/banned)
  • created_at, updated_at

  Script 表 - 脚本管理（独立实体，支持复用）
  • id (UUID PK), user_id (FK), conversation_id (FK, nullable)
  • title (脚本标题), content (Markdown内容)
  • source (uploaded/ai_generated/template)
  • generation_params (JSON: AI生成参数)
  • estimated_chars, estimated_duration
  • created_at

  Conversation 表 - AI对话会话（多轮交互生成脚本）
  • id (UUID PK), user_id (FK), script_id (FK, nullable)
  • title (对话标题), topic (原始话题)
  • style (educational/casual/interview), target_duration, speakers (JSON)
  • status (active/completed/abandoned)
  • message_count, total_tokens, total_cost
  • created_at, updated_at

  ConversationMessage 表 - 对话消息记录
  • id (UUID PK), conversation_id (FK)
  • role (user/assistant/system), content (消息内容)
  • metadata (JSON: model, tokens, cost, latency)
  • created_at

  Task 表 - 音频生成任务
  • id (UUID PK), user_id (FK), script_id (FK)
  • voice_config (JSON: {"daniu": "voice_id_1", "yifan": "voice_id_2"})
  • engine_type (mofa/direct_tts)
  • status (pending/processing/completed/failed)
  • progress (0-100), error_message
  • credit_cost, chars_processed
  • created_at, started_at, completed_at
  • retry_count, max_retries (default=1)

  Audio 表 - 音频文件（一个task可生成多个audio）
  • id (UUID PK), task_id (FK)
  • format (wav/mp3), file_path (本地或S3)
  • file_size, duration, sample_rate
  • created_at, expires_at (永久保留则null)

  CreditTransaction 表 - Credit流水
  • id (UUID PK), user_id (FK)
  • amount (正数=充值，负数=消费), balance_after
  • type (purchase/script_generation/audio_generation/refund)
  • reference_id (关联task_id或order_id)
  • description, created_at

  关系：
  • User 1:N Script, User 1:N Task, User 1:N CreditTransaction, User 1:N Conversation
  • Conversation 1:N ConversationMessage
  • Conversation 1:1 Script (可选，对话完成后生成)
  • Script 1:N Task
  • Task 1:N Audio

  4. 核心设计

  任务处理：

  • 异步：API返task_id，前端轮询 GET /api/tasks/{id}/status
  • 工作池：2-4个worker串行处理，避免GPU并发冲突
  • 重试：失败自动重试1次，超30分钟标记failed

  Worker 执行流程（MoFA 引擎）：
  1. 从 Redis 队列获取 task_id
  2. 查询数据库获取 Task 和 Script 信息
  3. 渲染 YAML 模板（根据 voice_config）→ 生成临时文件
  4. 保存脚本 Markdown 到临时文件：/tmp/tasks/task_{id}/script.md
  5. 启动 dora：subprocess.run(['dora', 'start', yaml_path])
  6. 启动动态节点：
     - script-segmenter --input-file script.md
     - voice-output --output-file output.wav
  7. 监控进程状态，更新 Task.progress
  8. 等待 voice-output 完成，获取 WAV 文件
  9. 转换为 MP3（ffmpeg）
  10. 保存 Audio 记录（2条：WAV + MP3）
  11. 扣除 credit，记录 CreditTransaction
  12. 清理 dora 进程（dora stop）
  13. 更新 Task.status = completed

  音频存储：

  • MVP：本地磁盘，按日期分目录
  • 预留：S3接口预留留，切换存储类即可
  • 双格式：同时生成WAV和MP3

  声音管理（动态 YAML 生成）：

  方案：Jinja2 模板渲染，每个任务独立配置
  • 维护模板文件：dataflow-minimax.template.yml
  • 用户提交任务时，根据 Task.voice_config JSON 渲染模板
  • 生成临时 YAML：/tmp/tasks/task_{task_id}.yml
  • 启动 dora 时指定临时 YAML 文件

  模板示例：
    env:
      MINIMAX_VOICE_ID: "{{ voice_config.daniu }}"
      MINIMAX_SPEED: "{{ voice_config.daniu_speed | default('1.0') }}"
      MINIMAX_PITCH: "{{ voice_config.daniu_pitch | default('0') }}"

  临时文件管理：
  • 任务完成后保留 24 小时（方便调试）
  • 定时任务每天凌晨清理 >24h 的临时文件
  • 并发任务互不干扰（每任务独立 YAML）

  声音库管理：
  • 前端展示可选声音列表（从 voices.yaml 读取）
  • 结构：voice_id, display_name, preview_url, language, category
  • 用户选择后保存到 Task.voice_config JSON 字段
  • 支持动态添加新声音（只需更新 voices.yaml）

  成本性能：

  • 单机4核8G，支持2-4并发
  • MiniMax费用：1000任务/天约300元/月
  • 缓存：相同请求缓存1小时，key是hash值

  5. AI Script 生成（多轮对话模式）

  对话流程：
  • 用户输入话题参数 → 创建 Conversation 记录
  • 多轮交互：用户追问 → AI优化脚本 → 保存到 ConversationMessage
  • 确认生成：最终内容保存到 Script 表，关联 conversation_id
  • 历史查看：用户可查看所有对话记录，继续编辑

  接口设计：
  • POST /api/conversations/create：创建对话会话
  • POST /api/conversations/{id}/messages：发送消息（多轮交互）
  • POST /api/conversations/{id}/finalize：确认生成脚本
  • GET /api/conversations：查看历史对话列表
  • PUT /api/conversations/{id}/resume：恢复对话继续编辑

  LLM 集成：
  • MVP：调用 OpenAI GPT-4 / Claude 3.5 Sonnet
  • 上下文管理：完整对话历史传入（控制在8k tokens内）
  • Prompt 模板化：支持不同风格（教育/闲聊/访谈）
  • 质量检查：验证说话人标记、字数、对话平衡

  Credit 计费（混合策略）：
  • AI对话：基础10 credit（前3轮），超出后每1000 tokens = 1 credit，上限50 credit/对话
  • 生成音频：按字数计费，100字 = 1 credit
  • 直接上传脚本：免费（不消耗credit）
  • 记录到CreditTransaction：type=script_generation, reference_id=conversation_id

  6. TTS 引擎可插拔设计

  核心：定义统一的 TTSEngine 抽象接口

  接口规范：
  • 输入：script 内容、voice_config 配置、输出目录、task_id
  • 输出：AudioResult 对象（wav_path, mp3_path, duration, chars_processed）
  • 方法：generate_audio、validate_voice_config

  DirectEngine（当前采用）：
  • 直接调用 MiniMax Python SDK
  • 复用 mofa/flows/podcast-generator 核心算法
    - script_segmenter.py:121-188 的脚本解析逻辑
    - script_segmenter.py:58-118 的智能分段算法
    - voice_output.py:78-89 的静音填充逻辑
  • 音频处理：numpy 拼接、scipy 保存 WAV、ffmpeg 转 MP3
  • 并发控制：asyncio.Semaphore 限制同时任务数

  MofaEngine（预留）：
  • Jinja2 渲染 dataflow-minimax.template.yml 模板
  • subprocess 启动 dora 数据流和动态节点
  • 监控进程状态，获取输出文件
  • 清理：停止 dora 进程，删除临时 YAML

  切换机制：
  • 配置文件指定 engine_type: "direct" 或 "mofa"
  • Worker 根据配置实例化不同引擎
  • 业务代码统一调用接口，不感知底层实现

  7. 技术实现要点

  前端架构：
  • 框架：Vue3 + ElementPlus
  • 登录认证：JWT token 存储于 localStorage
  • AI 对话：消息列表自动滚动，支持多轮交互
  • Markdown 编辑器：vue-markdown-editor，实时预览
  • 声音选择：el-select 下拉框，从 /api/voices 动态加载
  • 任务进度：el-progress 进度条，轮询查询（每 3 秒）
  • 音频下载：a 标签 download 属性支持双格式

  后端架构：
  • 框架：FastAPI + SQLAlchemy + Alembic
  • 认证：fastapi-jwt-auth，中间件验证 token
  • 数据库：PostgreSQL，7 张表（见第 3 节）
  • 异步任务：Redis 队列 + Worker 进程池

  AI 对话实现：
  • LLM 调用：OpenAI GPT-4 或 Claude 3.5 Sonnet
  • 上下文管理：读取 conversation_messages 历史（最近 20 条）
  • Prompt 模板化：根据 style 字段选择不同模板
  • Token 计费：记录 usage 到 metadata JSON 字段
  • 质量检查：正则验证说话人标记，确保至少 2 个角色

  音频生成流程：
  1. Redis 队列获取 task_id
  2. 查询 Task 和 Script 数据
  3. 解析 Markdown 脚本，提取说话人和文本
  4. 智能分段（长文本按标点切割）
  5. 串行调用 MiniMax TTS，生成音频片段
  6. 拼接音频数组，添加随机静音（0.3-1.2 秒）
  7. 保存 WAV 文件，转换 MP3
  8. 创建 Audio 记录（2 条），扣除 credit

  并发控制：
  • Redis 队列：任务放入队列等待处理
  • Worker 进程：启动 2-4 个独立进程（supervisord 管理）
  • 限流策略：每个 Worker 串行处理任务（避免 GPU 冲突）

  Credit 计费：
  • 原子性扣费：PostgreSQL 事务 + 行级锁（SELECT FOR UPDATE）
  • 余额不足拦截：中间件检查 credit_balance
  • 计费公式：
    - AI 对话：10 credit 基础费用（3 轮内）+ 超出 token 费用
    - 音频生成：按字符数计费（100 字 = 1 credit）
  • 流水记录：CreditTransaction 表记录所有变动

  8. 扩展预留

  多声音：voice_config 支持 {"daniu": "voice_1", "yifan": "voice_2", "boyu": "voice_3"}
  实时流式：WebSocket + Server-Sent Events（sse_starlette）
  脚本模板库：templates 表，预设 10+ 话题模板
  音频版本管理：同一 script_id 创建多个 task，不同 voice_config

  9. 部署

  • backend：FastAPI+MoFA
  • redis：队列缓存
  • worker：任务处理
  • nginx：反向代理+SSL
  • frontend：Vue静态页面

  audio存音频，logs存日志，redis_data持久化队列
  预留K8s配置，数据库扩到PostgreSQL
