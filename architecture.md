# MoFA FM 架构设计

## 系统总览架构图

```mermaid
graph TB
    subgraph "🎨 前端层 Frontend Layer"
        subgraph "Vue 3 + Vite 应用"
            Home[Home.vue<br/>首页 - 播客推荐]
            Discover[Discover.vue<br/>发现 - 分类浏览]
            Search[Search.vue<br/>搜索页面]
            Library[Library.vue<br/>我的收藏]

            subgraph "创作者工作台"
                Dashboard[Creator Dashboard<br/>创作者仪表盘]
                UI[AIScriptStudio.vue<br/>🤖 AI 脚本创作工作室]
                CreateShow[CreateShow.vue<br/>创建节目]
                ManageShow[ManageShow.vue<br/>管理节目]
            end

            ShowDetail[ShowDetail.vue<br/>节目详情页]
            EpisodeDetail[EpisodeDetail.vue<br/>单集详情页]
            Player[GlobalPlayer.vue<br/>🎵 全局播放器]

            subgraph "Pinia 状态管理"
                AuthStore[auth.js<br/>用户认证状态]
                PlayerStore[player.js<br/>播放器状态]
                PodcastStore[podcasts.js<br/>播客数据缓存]
            end
        end
    end

    subgraph "🔧 后端层 Backend Layer"
        subgraph "Django REST Framework"
            Router[URL Router<br/>config/urls.py]

            subgraph "API ViewSets"
                UserAPI[users/api/<br/>用户注册登录<br/>创作者验证]
                PodcastAPI[podcasts/api/<br/>节目管理<br/>单集管理<br/>分类标签]
                ScriptAPI[podcasts/api/<br/>🎯 ScriptSession API<br/>AI 脚本会话]
                InteractionAPI[interactions/api/<br/>评论点赞关注<br/>播放历史]
                SearchAPI[search/api/<br/>全文搜索]
            end

            subgraph "Service Layer"
                FileParser[file_parser.py<br/>📄 文件解析服务<br/>PDF/DOCX/TXT/MD]
                ScriptAI[script_ai.py<br/>🤖 AI 对话服务<br/>⚠️ 待替换为 MoFA]
                AudioProc[audio_processor.py<br/>🎵 音频处理<br/>⚠️ 待替换为 MoFA]
            end

            subgraph "Django Models"
                User[User<br/>用户模型]
                Show[Show<br/>播客节目]
                Episode[Episode<br/>播客单集]
                ScriptSession[ScriptSession<br/>AI 脚本会话]
                UploadRef[UploadedReference<br/>参考文件]
                Comment[Comment<br/>评论 MPTT 树]
                Follow[Follow/Like<br/>互动关系]
                PlayHistory[PlayHistory<br/>播放历史]
            end
        end

        subgraph "任务队列"
            Celery[Celery Worker<br/>异步任务处理]
            CeleryBeat[Celery Beat<br/>定时任务调度]
        end
    end

    subgraph "🔄 MoFA 数据流层 DataFlow Layer"
        subgraph "Dora Runtime 运行时"
            DoraCore[Dora Core<br/>Rust 数据流引擎<br/>节点通信管理]
        end

        subgraph "💬 AI 对话数据流"
            subgraph "openai_chat_dataflow.yml"
                TI1[terminal-input<br/>🔷 动态节点<br/>─────────<br/>接收: Django 消息<br/>发送: query<br/>接收: llm_result<br/>返回: Django API]

                OAI[openai_chat_agent<br/>🔶 静态节点<br/>─────────<br/>输入: query<br/>处理: 调用 LLM API<br/>输出: llm_result]
            end
        end

        subgraph "🎙️ 播客生成数据流"
            subgraph "podcast_dataflow.yml"
                SS[script-segmenter<br/>🔷 动态节点<br/>─────────<br/>接收: Markdown 脚本<br/>解析: 【角色】标签<br/>分段: 智能分割长文本<br/>输出: 角色_text<br/>      script_complete]

                subgraph "TTS 引擎节点组"
                    TTS1[minimax-daniu<br/>🔶 静态节点<br/>─────────<br/>音色: 大牛 刘翔<br/>输入: daniu_text<br/>调用: MiniMax API<br/>批次: 2s audio chunks<br/>输出: audio, segment_complete]

                    TTS2[minimax-yifan<br/>🔶 静态节点<br/>─────────<br/>音色: 一帆 豆包<br/>输入: yifan_text<br/>调用: MiniMax API<br/>批次: 2s audio chunks<br/>输出: audio, segment_complete]

                    TTS3[minimax-boyu<br/>🔶 静态节点<br/>─────────<br/>音色: 博宇<br/>输入: boyu_text<br/>调用: MiniMax API<br/>批次: 2s audio chunks<br/>输出: audio, segment_complete]
                end

                VO[voice-output<br/>🔷 动态节点<br/>─────────<br/>输入: 多路 audio + segment_complete<br/>处理: 角色切换检测<br/>      随机静音 0.3-1.2s<br/>      音频拼接 numpy<br/>输出: 最终 WAV 文件<br/>队列: queue_size=1000]

                Viewer[viewer<br/>🔷 动态节点<br/>─────────<br/>接收: 所有 log 输出<br/>显示: 实时彩色日志<br/>监控: 节点状态<br/>可选: 调试用]
            end
        end
    end

    subgraph "💾 存储层 Storage Layer"
        DB[(PostgreSQL<br/>─────────<br/>• 用户数据<br/>• 播客元数据<br/>• 脚本会话<br/>• 对话历史<br/>• 评论互动<br/>• 播放记录)]

        Redis[(Redis<br/>─────────<br/>• Celery 队列<br/>• 会话缓存<br/>• 播放进度<br/>• 搜索缓存)]

        Media[Media 文件存储<br/>─────────<br/>• 播客音频 WAV/MP3<br/>• 节目封面图<br/>• 用户头像<br/>• 参考文件 PDF/DOCX]
    end

    subgraph "🌐 外部服务 External Services"
        Kimi[Kimi AI API<br/>─────────<br/>模型: Moonshot<br/>用途: LLM 对话生成<br/>      脚本创作<br/>上下文: 8k tokens]

        MiniMax[MiniMax T2A API<br/>─────────<br/>服务: 文本转语音<br/>音色: 多种中文声音<br/>格式: PCM 32kHz 16bit<br/>流式: WebSocket 推送]
    end

    %% ═══════════════ 数据流连接 ═══════════════

    %% 前端到后端 HTTP/WebSocket
    Home & Discover & Search & Library -->|GET /api/podcasts/| PodcastAPI
    ShowDetail & EpisodeDetail -->|GET /api/podcasts/shows/| PodcastAPI
    UI -->|POST /api/script-sessions/:id/chat/| ScriptAPI
    UI -->|POST /api/script-sessions/:id/generate_audio/| ScriptAPI
    UI -->|POST /api/script-sessions/:id/upload_file/| ScriptAPI
    Dashboard -->|GET /api/podcasts/my-shows/| PodcastAPI
    Player -->|POST /api/interactions/play/update/| InteractionAPI

    %% 前端状态管理
    UI & Dashboard & ShowDetail -.-> AuthStore & PlayerStore & PodcastStore

    %% 后端路由
    Router --> UserAPI & PodcastAPI & ScriptAPI & InteractionAPI & SearchAPI

    %% API 到 Service
    ScriptAPI -->|调用| FileParser
    ScriptAPI -->|⚠️ 待移除| ScriptAI
    PodcastAPI -->|⚠️ 待移除| AudioProc

    %% Service 到 Models
    UserAPI --> User
    PodcastAPI --> Show & Episode
    ScriptAPI --> ScriptSession & UploadRef
    InteractionAPI --> Comment & Follow & PlayHistory

    %% Models 到数据库
    User & Show & Episode & ScriptSession & UploadRef & Comment & Follow & PlayHistory --> DB

    %% 后端触发 MoFA 数据流 (虚线 = 未来实现)
    ScriptAPI -.->|🔜 触发 AI 对话流<br/>传递: chat_history + uploaded_files| DoraCore
    ScriptAPI -.->|🔜 触发播客生成流<br/>传递: current_script + voice_config| DoraCore

    %% Dora 管理数据流
    DoraCore --> TI1 & OAI
    DoraCore --> SS & TTS1 & TTS2 & TTS3 & VO & Viewer

    %% AI 对话流内部
    TI1 <-->|query| OAI
    OAI -->|API 请求| Kimi
    Kimi -->|AI 回复| OAI
    TI1 -.->|llm_result| ScriptAPI

    %% 播客生成流内部
    SS -->|daniu_text| TTS1
    SS -->|yifan_text| TTS2
    SS -->|boyu_text| TTS3
    SS -->|script_complete| VO

    TTS1 & TTS2 & TTS3 -->|API 请求| MiniMax
    MiniMax -->|音频流 PCM| TTS1 & TTS2 & TTS3

    TTS1 -->|audio + segment_complete| VO
    TTS2 -->|audio + segment_complete| VO
    TTS3 -->|audio + segment_complete| VO

    SS & TTS1 & TTS2 & TTS3 & VO -->|log| Viewer

    VO -.->|生成的 WAV<br/>保存路径| Media
    Media -.->|文件路径| ScriptAPI
    ScriptAPI -.->|更新 Episode.audio_file<br/>status=published| Episode

    %% 文件上传
    FileParser --> Media
    UploadRef --> Media

    %% 异步任务
    PodcastAPI & InteractionAPI --> Celery
    Celery --> Redis
    CeleryBeat --> Celery

    %% 缓存
    ScriptAPI & PodcastAPI & InteractionAPI <--> Redis

    %% ═══════════════ 样式定义 ═══════════════
    classDef frontend fill:#6dcad0,stroke:#333,stroke-width:3px,color:#000
    classDef backend fill:#ffc63e,stroke:#333,stroke-width:3px,color:#000
    classDef mofa fill:#ff513b,stroke:#333,stroke-width:3px,color:#fff
    classDef storage fill:#fd553f,stroke:#333,stroke-width:3px,color:#fff
    classDef external fill:#b4a7d6,stroke:#333,stroke-width:3px,color:#000
    classDef deprecated fill:#ffa07a,stroke:#d00,stroke-width:2px,stroke-dasharray: 5 5,color:#000

    class Home,Discover,Search,Library,Dashboard,UI,CreateShow,ManageShow,ShowDetail,EpisodeDetail,Player,AuthStore,PlayerStore,PodcastStore frontend
    class Router,UserAPI,PodcastAPI,ScriptAPI,InteractionAPI,SearchAPI,FileParser,User,Show,Episode,ScriptSession,UploadRef,Comment,Follow,PlayHistory,Celery,CeleryBeat backend
    class DoraCore,TI1,OAI,SS,TTS1,TTS2,TTS3,VO,Viewer mofa
    class DB,Redis,Media storage
    class Kimi,MiniMax external
    class ScriptAI,AudioProc deprecated
```

## 数据流详解

### 1. AI 对话流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Vue as Vue 前端
    participant Django as Django API
    participant Dora as Dora Runtime
    participant TI as terminal-input
    participant OAI as openai_chat_agent
    participant Kimi as Kimi AI

    User->>Vue: 输入消息"帮我写个播客脚本"
    Vue->>Django: POST /script-sessions/1/chat/

    Django->>Django: 1. 查询 ScriptSession
    Django->>Django: 2. 获取对话历史 + 参考文件

    Django->>Dora: 触发 openai_chat_dataflow
    Dora->>TI: 启动动态节点

    Django->>TI: 发送消息 + 上下文
    TI->>OAI: query (含对话历史)
    OAI->>Kimi: API 调用
    Kimi-->>OAI: AI 生成结果
    OAI->>TI: llm_result
    TI-->>Django: 返回 AI 回复

    Django->>Django: 3. 保存对话历史
    Django->>Django: 4. 提取并更新脚本
    Django-->>Vue: 响应: {reply, script}
    Vue-->>User: 显示 AI 回复和脚本
```

### 2. 播客生成流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Vue as Vue 前端
    participant Django as Django API
    participant Dora as Dora Runtime
    participant SS as script-segmenter
    participant TTS as minimax-tts (x3)
    participant VO as voice-output
    participant MiniMax as MiniMax API
    participant Storage as 文件存储

    User->>Vue: 点击"生成播客"
    Vue->>Django: POST /script-sessions/1/generate_audio/

    Django->>Django: 1. 获取 current_script (Markdown)
    Django->>Django: 2. 获取 voice_config (音色配置)
    Django->>Django: 3. 创建 Episode (status=processing)

    Django->>Dora: 触发 podcast_dataflow
    Dora->>SS: 启动 script-segmenter
    Dora->>TTS: 启动 minimax-daniu/yifan/boyu
    Dora->>VO: 启动 voice-output

    Django->>SS: 发送 Markdown 脚本
    SS->>SS: 解析脚本，按【角色】分段

    loop 每个文本段
        SS->>TTS: 发送文本 (daniu_text/yifan_text/boyu_text)
        TTS->>MiniMax: TTS API 调用
        MiniMax-->>TTS: 音频流 (批次 2s)
        TTS->>VO: 音频数据 + segment_complete
        VO->>VO: 检测角色切换，添加随机静音
        VO->>VO: 拼接音频片段
        SS->>SS: 等待 segment_complete 信号
    end

    SS->>VO: script_complete (所有段落完成)
    VO->>VO: 写入最终 WAV 文件
    VO->>Storage: 保存 podcast_output.wav

    VO-->>Django: 返回音频文件路径
    Django->>Django: 更新 Episode (status=published, audio_file=...)
    Django-->>Vue: 返回成功 + Episode 详情
    Vue-->>User: 显示"生成完成"，可播放
```

### 3. 文件上传流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Vue as Vue 前端
    participant Django as Django API
    participant Parser as FileParser 服务
    participant Storage as 文件存储
    participant DB as 数据库

    User->>Vue: 上传参考文件 (PDF/DOCX/TXT/MD)
    Vue->>Django: POST /script-sessions/1/upload_file/

    Django->>Storage: 保存原始文件
    Django->>Parser: 解析文件内容

    alt PDF 文件
        Parser->>Parser: PyPDF2 提取文本
    else DOCX 文件
        Parser->>Parser: python-docx 提取文本
    else TXT/MD 文件
        Parser->>Parser: 直接读取文本
    end

    Parser-->>Django: 返回 extracted_text
    Django->>DB: 创建 UploadedReference 记录
    Django-->>Vue: 返回文件信息
    Vue-->>User: 显示"上传成功"

    Note over Django,Parser: extracted_text 将在下次 AI 对话时<br/>作为上下文传递给 LLM
```

## 技术栈总结

| 层级 | 技术 | 作用 |
|------|------|------|
| **前端** | Vue 3 + Vite + Pinia | 用户界面，状态管理 |
| **后端** | Django 5.1 + DRF | API 服务，业务逻辑，数据库 ORM |
| **数据流** | MoFA + Dora (Rust) | 数据流编排，节点通信 |
| **AI 对话** | openai_chat_agent + Kimi API | LLM 对话生成 |
| **语音合成** | minimax-t2a + MiniMax API | 文本转语音 (TTS) |
| **音频处理** | script-segmenter + voice-output | 脚本解析，音频拼接 |
| **数据库** | PostgreSQL / SQLite | 持久化存储 |
| **缓存/队列** | Redis + Celery | 异步任务，缓存 |
| **文件存储** | 本地 Media 文件系统 | 音频、图片、文档 |

## 核心设计原则

### 1. **关注点分离**
- **Django**: 负责业务逻辑、数据管理、用户认证
- **MoFA**: 负责计算密集型任务 (AI 对话、TTS 生成)
- **前端**: 负责用户交互、状态展示

### 2. **数据流驱动**
- 使用 MoFA 的数据流范式，将复杂任务拆解为独立节点
- 节点间通过定义良好的输入/输出通道通信
- 支持动态节点 (Python) 和静态节点 (Dora 管理)

### 3. **异步与实时**
- **AI 对话**: 可选 WebSocket 实现流式响应
- **音频生成**: 异步任务，前端轮询或 WebSocket 推送进度
- **播放器**: 实时播放，进度保存

### 4. **模块化与可扩展**
- 新增音色：只需修改 dataflow.yml 的 `env.MINIMAX_VOICE_ID`
- 新增角色：在 script-segmenter 的 `character_aliases` 添加映射
- 新增 LLM：替换 openai_chat_agent 的 API 配置

### 5. **错误处理与监控**
- MoFA 节点：使用 `send_log()` 输出日志
- Django：使用 DRF 异常处理
- Viewer 节点：实时监控数据流执行状态

## MoFA 数据流节点详解

### openai_chat_agent 节点内部结构

```mermaid
graph TB
    subgraph "openai_chat_agent 节点 (MofaAgent)"
        Input[输入通道<br/>query]

        subgraph "main.py 处理流程"
            Receive[1. receive_parameter<br/>接收 query 数据]
            LoadEnv[2. load_dotenv<br/>加载环境变量]

            subgraph "call_openai_directly 函数"
                InitClient[3. 初始化 OpenAI Client<br/>api_key: LLM_API_KEY<br/>base_url: LLM_API_BASE]
                CreateMsg[4. 构建消息列表<br/>system + user]
                CallAPI[5. client.chat.completions.create<br/>model: LLM_MODEL]
                Extract[6. 提取 response.choices[0].message.content]
            end

            SendOut[7. send_output<br/>agent_output_name: llm_result]
            Log[8. write_log<br/>记录日志]
        end

        Output[输出通道<br/>llm_result]

        Input --> Receive
        Receive --> LoadEnv
        LoadEnv --> InitClient
        InitClient --> CreateMsg
        CreateMsg --> CallAPI
        CallAPI --> Extract
        Extract --> SendOut
        SendOut --> Output
        Receive & CallAPI & SendOut --> Log
    end

    Kimi[Kimi AI API<br/>https://api.moonshot.cn]

    CallAPI -->|HTTPS POST| Kimi
    Kimi -->|JSON Response| Extract

    classDef process fill:#ffc63e,stroke:#333,stroke-width:2px
    classDef io fill:#6dcad0,stroke:#333,stroke-width:2px
    classDef external fill:#b4a7d6,stroke:#333,stroke-width:2px

    class Receive,LoadEnv,InitClient,CreateMsg,CallAPI,Extract,SendOut,Log process
    class Input,Output io
    class Kimi external
```

### podcast-generator 数据流时序图

```mermaid
sequenceDiagram
    autonumber

    participant Django as Django API
    participant Dora as Dora Runtime
    participant SS as script-segmenter
    participant TTS1 as minimax-daniu
    participant TTS2 as minimax-yifan
    participant TTS3 as minimax-boyu
    participant MiniMax as MiniMax API
    participant VO as voice-output
    participant Viewer as viewer
    participant Storage as 文件存储

    Note over Django: 用户点击"生成播客"

    Django->>Django: 获取 ScriptSession
    Django->>Django: 读取 current_script (Markdown)
    Django->>Django: 读取 voice_config (音色映射)
    Django->>Django: 创建 Episode (status=processing)

    Django->>Dora: 启动 podcast_dataflow.yml

    activate Dora
    Dora->>TTS1: 启动静态节点 (Luo Xiang voice)
    Dora->>TTS2: 启动静态节点 (Doubao voice)
    Dora->>TTS3: 启动静态节点 (Boyu voice)

    Dora->>SS: 启动动态节点 (Python)
    activate SS

    Dora->>VO: 启动动态节点 (Python)
    activate VO

    Dora->>Viewer: 启动动态节点 (可选)
    activate Viewer

    Django->>SS: 发送 Markdown 脚本

    SS->>SS: parse_markdown()<br/>识别【大牛】【一帆】【博宇】
    SS->>SS: split_long_text()<br/>按标点符号智能分段<br/>max_length=45字

    Note over SS: 假设解析出 5 个段落

    loop 顺序处理每个段落
        alt 段落属于【大牛】
            SS->>TTS1: 发送 daniu_text
            TTS1->>MiniMax: POST /text_to_speech<br/>voice_id: ttv-voice-xxx<br/>text: "..."
            MiniMax-->>TTS1: 音频流 (2s 批次)
            TTS1->>VO: audio (fragment_num: 1, 2, 3...)
            TTS1->>VO: segment_complete
            TTS1->>Viewer: log: "生成大牛音频"
            VO->>VO: 检测角色切换<br/>添加 0.3-1.2s 随机静音
            VO->>Viewer: log: "添加 0.8s 静音"
            VO->>SS: daniu_segment_complete
        else 段落属于【一帆】
            SS->>TTS2: 发送 yifan_text
            TTS2->>MiniMax: POST /text_to_speech<br/>voice_id: moss_audio_xxx<br/>text: "..."
            MiniMax-->>TTS2: 音频流 (2s 批次)
            TTS2->>VO: audio (fragment_num: 1, 2, 3...)
            TTS2->>VO: segment_complete
            TTS2->>Viewer: log: "生成一帆音频"
            VO->>VO: 检测角色切换<br/>添加随机静音
            VO->>Viewer: log: "添加 1.1s 静音"
            VO->>SS: yifan_segment_complete
        else 段落属于【博宇】
            SS->>TTS3: 发送 boyu_text
            TTS3->>MiniMax: POST /text_to_speech
            MiniMax-->>TTS3: 音频流
            TTS3->>VO: audio + segment_complete
            TTS3->>Viewer: log: "生成博宇音频"
            VO->>SS: boyu_segment_complete
        end

        SS->>Viewer: log: "段落 X 完成"
    end

    SS->>VO: script_complete
    SS->>Viewer: log: "所有段落完成"

    VO->>VO: 拼接所有音频片段<br/>numpy.concatenate()
    VO->>VO: 写入 WAV 文件<br/>scipy.io.wavfile.write()
    VO->>Storage: 保存 podcast_output.wav
    VO->>Viewer: log: "保存成功 45.32s"

    VO-->>Django: 返回文件路径

    deactivate VO
    deactivate SS
    deactivate Viewer
    deactivate Dora

    Django->>Django: 更新 Episode<br/>audio_file = "/media/...wav"<br/>status = "published"<br/>duration = 45

    Django-->>Django: 返回成功响应

    Note over Django: 前端轮询或 WebSocket 通知<br/>播客生成完成
```

## Django 与 MoFA 集成架构

### 集成方式对比

```mermaid
graph TB
    subgraph "方案 A: 直接集成 (推荐)"
        DjangoA[Django API]
        subgraph "Python 子进程"
            MofaAgentA[MofaAgent<br/>Python 实例]
            DoraNodeA[Dora Node<br/>连接到 Runtime]
        end

        DjangoA -->|subprocess.Popen| MofaAgentA
        MofaAgentA -->|PyArrow| DoraNodeA
        DoraNodeA -.->|返回结果| DjangoA
    end

    subgraph "方案 B: HTTP API 桥接"
        DjangoB[Django API]
        Bridge[MoFA Bridge Service<br/>FastAPI/Flask]
        MofaAgentB[MofaAgent<br/>后台常驻]

        DjangoB -->|HTTP POST| Bridge
        Bridge -->|触发数据流| MofaAgentB
        MofaAgentB -.->|HTTP Response| Bridge
        Bridge -.->|返回结果| DjangoB
    end

    subgraph "方案 C: 消息队列解耦 (生产推荐)"
        DjangoC[Django API]
        CeleryTask[Celery Task]
        MQ[RabbitMQ/Redis]
        MofaAgentC[MofaAgent Worker]

        DjangoC -->|异步任务| CeleryTask
        CeleryTask -->|发布消息| MQ
        MQ -->|订阅消息| MofaAgentC
        MofaAgentC -.->|结果回调| DjangoC
    end

    classDef django fill:#ffc63e,stroke:#333,stroke-width:2px
    classDef mofa fill:#ff513b,stroke:#333,stroke-width:2px,color:#fff
    classDef infra fill:#b4a7d6,stroke:#333,stroke-width:2px

    class DjangoA,DjangoB,DjangoC,CeleryTask django
    class MofaAgentA,MofaAgentB,MofaAgentC,DoraNodeA mofa
    class Bridge,MQ infra
```

### 方案 C 实现细节 (推荐生产环境)

```mermaid
sequenceDiagram
    participant User as 用户
    participant Django as Django API
    participant Celery as Celery Worker
    participant Redis as Redis Queue
    participant MofaWorker as MoFA Worker
    participant Dora as Dora Runtime
    participant DB as 数据库
    participant WS as WebSocket Server

    User->>Django: POST /script-sessions/1/generate_audio/

    Django->>DB: 创建 Episode (status=queued)
    Django->>Celery: generate_podcast_task.delay(episode_id)
    Django-->>User: 返回 202 Accepted<br/>{task_id, episode_id}

    Celery->>Redis: 推送任务到队列

    Note over User,Django: 用户可以继续其他操作

    Redis-->>MofaWorker: 拉取任务

    MofaWorker->>DB: 更新 Episode (status=processing)
    MofaWorker->>WS: 推送进度 0%

    MofaWorker->>Dora: 启动 podcast_dataflow

    activate Dora
    Dora->>Dora: 执行 TTS 生成流程

    loop 每个段落完成
        Dora->>MofaWorker: 返回进度
        MofaWorker->>WS: 推送进度 25%/50%/75%
    end

    Dora-->>MofaWorker: 返回音频文件路径
    deactivate Dora

    MofaWorker->>DB: 更新 Episode<br/>(status=published, audio_file=...)
    MofaWorker->>WS: 推送进度 100%
    MofaWorker->>Redis: 标记任务完成

    WS-->>User: 通知播客生成完成
    User->>Django: GET /episodes/{id}/
    Django-->>User: 返回完整 Episode 数据
```

## 数据模型关系图

```mermaid
erDiagram
    USER ||--o{ SHOW : creates
    USER ||--o{ SCRIPT_SESSION : owns
    USER ||--o{ COMMENT : writes
    USER ||--o{ FOLLOW : follows
    USER ||--o{ LIKE : likes
    USER ||--o{ PLAY_HISTORY : plays
    USER {
        int id PK
        string username UK
        string email UK
        string avatar
        bool is_creator
        bool is_verified
        int shows_count
        datetime created_at
    }

    SHOW ||--o{ EPISODE : contains
    SHOW ||--o{ SCRIPT_SESSION : relates
    SHOW }o--|| CATEGORY : belongs_to
    SHOW }o--o{ TAG : tagged_with
    SHOW ||--o{ FOLLOW : followed_by
    SHOW {
        int id PK
        string title
        string slug UK
        text description
        string cover
        string content_type
        int creator_id FK
        int category_id FK
        int episodes_count
        int followers_count
        datetime created_at
    }

    EPISODE ||--o{ COMMENT : receives
    EPISODE ||--o{ LIKE : liked_by
    EPISODE ||--o{ PLAY_HISTORY : played_in
    EPISODE ||--o| SCRIPT_SESSION : generated_from
    EPISODE {
        int id PK
        int show_id FK
        string title
        string slug
        text description
        string audio_file
        int duration
        string status
        int play_count
        int like_count
        datetime published_at
    }

    SCRIPT_SESSION ||--o{ UPLOADED_REFERENCE : has
    SCRIPT_SESSION {
        int id PK
        int creator_id FK
        int show_id FK
        int episode_id FK
        string title
        string status
        json chat_history
        text current_script
        json script_versions
        json voice_config
        datetime created_at
    }

    UPLOADED_REFERENCE {
        int id PK
        int session_id FK
        string file
        string original_filename
        string file_type
        text extracted_text
        datetime uploaded_at
    }

    COMMENT ||--o{ COMMENT : replies_to
    COMMENT {
        int id PK
        int episode_id FK
        int user_id FK
        int parent_id FK
        text text
        int timestamp
        int lft
        int rght
        int tree_id
        datetime created_at
    }

    CATEGORY {
        int id PK
        string name UK
        string slug UK
        string icon
        string color
        int order
    }

    TAG {
        int id PK
        string name UK
        string slug UK
    }

    FOLLOW {
        int id PK
        int user_id FK
        int show_id FK
        datetime created_at
    }

    LIKE {
        int id PK
        int user_id FK
        int episode_id FK
        datetime created_at
    }

    PLAY_HISTORY {
        int id PK
        int user_id FK
        int episode_id FK
        int position
        bool completed
        datetime last_played_at
    }
```

## 部署架构

```mermaid
graph TB
    subgraph "用户层"
        Browser[Web 浏览器<br/>Vue 3 SPA]
        Mobile[移动端<br/>未来支持]
    end

    subgraph "CDN 层"
        CDN[CDN<br/>静态资源分发<br/>• JS/CSS Bundle<br/>• 图片<br/>• 音频文件]
    end

    subgraph "负载均衡层"
        LB[Nginx<br/>负载均衡 + SSL<br/>─────────<br/>• HTTPS 终结<br/>• WebSocket 升级<br/>• 静态文件服务<br/>• Gzip 压缩]
    end

    subgraph "应用层 (Kubernetes Cluster)"
        subgraph "Django Pod 1"
            Django1[Django + Gunicorn<br/>Web 服务器]
            DjangoCelery1[Celery Worker<br/>异步任务]
        end

        subgraph "Django Pod 2"
            Django2[Django + Gunicorn<br/>Web 服务器]
            DjangoCelery2[Celery Worker<br/>异步任务]
        end

        CeleryBeat[Celery Beat<br/>定时任务调度器<br/>单实例]

        subgraph "MoFA Worker Pool"
            MofaWorker1[MoFA Worker 1<br/>AI 对话 + 播客生成]
            MofaWorker2[MoFA Worker 2<br/>AI 对话 + 播客生成]
            MofaWorker3[MoFA Worker 3<br/>AI 对话 + 播客生成]
        end

        WSServer[WebSocket Server<br/>Django Channels<br/>─────────<br/>• 实时进度推送<br/>• 聊天通知]
    end

    subgraph "数据层"
        DBMaster[(PostgreSQL<br/>主库<br/>─────────<br/>写入 + 读取)]
        DBSlave1[(PostgreSQL<br/>从库 1<br/>─────────<br/>只读)]
        DBSlave2[(PostgreSQL<br/>从库 2<br/>─────────<br/>只读)]

        RedisCluster[(Redis Cluster<br/>─────────<br/>• Celery 队列<br/>• 会话缓存<br/>• 播放进度<br/>• WebSocket 状态)]
    end

    subgraph "存储层"
        S3[对象存储<br/>AWS S3 / 阿里云 OSS<br/>─────────<br/>• 播客音频 (WAV/MP3)<br/>• 封面图片<br/>• 用户头像<br/>• 参考文件]
    end

    subgraph "外部服务"
        Kimi[Kimi AI API<br/>LLM 对话]
        MiniMax[MiniMax T2A<br/>语音合成]
    end

    subgraph "监控层"
        Prometheus[Prometheus<br/>指标采集]
        Grafana[Grafana<br/>可视化监控]
        ELK[ELK Stack<br/>日志聚合]
    end

    %% 用户请求路径
    Browser --> CDN
    Mobile --> CDN
    CDN --> LB

    LB --> Django1 & Django2
    LB --> WSServer

    %% Django 到数据库
    Django1 & Django2 -->|写入| DBMaster
    Django1 & Django2 -->|读取| DBSlave1 & DBSlave2
    DBMaster -->|主从复制| DBSlave1 & DBSlave2

    %% Django 到 Redis
    Django1 & Django2 <--> RedisCluster
    WSServer <--> RedisCluster

    %% Django 到 Celery
    Django1 & Django2 -->|推送任务| RedisCluster
    RedisCluster -->|拉取任务| DjangoCelery1 & DjangoCelery2
    CeleryBeat -->|定时触发| RedisCluster

    %% Celery 到 MoFA
    DjangoCelery1 & DjangoCelery2 -->|AI/TTS 任务| RedisCluster
    RedisCluster -->|拉取任务| MofaWorker1 & MofaWorker2 & MofaWorker3

    %% MoFA 到外部服务
    MofaWorker1 & MofaWorker2 & MofaWorker3 -->|API 调用| Kimi & MiniMax

    %% 文件存储
    Django1 & Django2 <--> S3
    MofaWorker1 & MofaWorker2 & MofaWorker3 --> S3
    CDN <--> S3

    %% 监控
    Django1 & Django2 & DjangoCelery1 & DjangoCelery2 --> Prometheus
    MofaWorker1 & MofaWorker2 & MofaWorker3 --> Prometheus
    DBMaster & RedisCluster --> Prometheus
    Prometheus --> Grafana

    Django1 & Django2 & MofaWorker1 & MofaWorker2 --> ELK

    %% 样式
    classDef user fill:#e1f5ff,stroke:#333,stroke-width:2px
    classDef infra fill:#fff3cd,stroke:#333,stroke-width:2px
    classDef app fill:#ffc63e,stroke:#333,stroke-width:3px
    classDef mofa fill:#ff513b,stroke:#333,stroke-width:3px,color:#fff
    classDef data fill:#fd553f,stroke:#333,stroke-width:2px,color:#fff
    classDef external fill:#b4a7d6,stroke:#333,stroke-width:2px
    classDef monitor fill:#d4edda,stroke:#333,stroke-width:2px

    class Browser,Mobile user
    class CDN,LB,WSServer infra
    class Django1,Django2,DjangoCelery1,DjangoCelery2,CeleryBeat app
    class MofaWorker1,MofaWorker2,MofaWorker3 mofa
    class DBMaster,DBSlave1,DBSlave2,RedisCluster,S3 data
    class Kimi,MiniMax external
    class Prometheus,Grafana,ELK monitor
```

## 关键优化点

### 1. **性能优化**
- **音频批处理**: MiniMax TTS 使用 2s 批次，减少消息数量 (200+ → 3-4)
- **队列缓冲**: voice-output 使用 queue_size=1000，防止音频丢包
- **数据库索引**: 对高频查询字段建立索引 (created_at, status 等)

### 2. **成本优化**
- **缓存策略**: Redis 缓存热门播客、用户会话
- **API 调用**: 批量 TTS 请求，减少 API 调用次数
- **存储分层**: 冷数据迁移至对象存储

### 3. **用户体验**
- **流式响应**: AI 对话支持流式输出
- **进度反馈**: 音频生成实时进度条
- **断点续传**: 长时间生成任务支持恢复

---

**架构版本**: v2.0
**更新日期**: 2025-11-24
**设计理念**: MoFA 数据流 + Django 业务逻辑 + Vue 用户界面
