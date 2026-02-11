<template>
    <div class="ai-script-studio">
        <div class="container">
            <div class="page-head">
                <h1 class="page-title">AI 音频创作</h1>
                <router-link
                    v-if="!currentSession"
                    to="/creator/rss-automation"
                    class="mofa-btn mofa-btn-warning page-head-btn"
                >
                    RSS 自动化
                </router-link>
            </div>

            <!-- 会话列表视图 -->
            <div v-if="!currentSession" class="session-list-view">
                <div class="entry-hub mofa-card">
                    <div class="entry-header">
                        <div>
                            <h2>开始创作</h2>
                            <p class="entry-subtitle"></p>
                        </div>
                        <div class="entry-header-links">
                            <router-link to="/creator/shows/create" class="section-link">
                                新建节目
                            </router-link>
                            <router-link
                                v-if="entryMode === 'debate'"
                                to="/debates"
                                class="section-link"
                            >
                                查看辩论历史
                            </router-link>
                        </div>
                    </div>

                    <div class="mode-tabs">
                        <button
                            class="mode-tab"
                            :class="{ active: entryMode === 'dialogue' }"
                            @click="entryMode = 'dialogue'"
                        >
                            对话脚本
                        </button>
                        <button
                            class="mode-tab"
                            :class="{ active: entryMode === 'debate' }"
                            @click="entryMode = 'debate'"
                        >
                            辩论 / 会议
                        </button>
                        <button
                            class="mode-tab"
                            :class="{ active: entryMode === 'rss' }"
                            @click="entryMode = 'rss'"
                        >
                            RSS 生成
                        </button>
                    </div>

                    <div v-if="entryMode === 'dialogue'" class="mode-panel">
                        <p class="section-tip">
                            以对话迭代脚本，支持上传参考资料，再一键转音频。
                        </p>
                        <div class="actions">
                            <button
                                @click="createNewSession"
                                class="mofa-btn mofa-btn-primary"
                            >
                                新建对话会话
                            </button>
                        </div>

                        <div v-if="loading" class="loading-state">
                            加载中...
                        </div>

                        <div
                            v-else-if="sessions.length === 0"
                            class="empty-state"
                        >
                            <p>还没有创作会话</p>
                            <p class="hint">先新建一个会话即可开始。</p>
                        </div>

                        <div v-else class="sessions-grid">
                            <div
                                v-for="session in sessions"
                                :key="session.id"
                                class="session-card mofa-card"
                                @click="loadSession(session.id)"
                            >
                                <div class="session-header">
                                    <h3 class="session-title">
                                        {{ session.title }}
                                    </h3>
                                    <button
                                        class="delete-button"
                                        @click.stop="
                                            confirmDeleteSession(session.id)
                                        "
                                    >
                                        删除
                                    </button>
                                </div>
                                <div class="session-meta">
                                    <span>{{
                                        formatDate(session.created_at)
                                    }}</span>
                                    <span
                                        >{{
                                            session.chat_history?.length || 0
                                        }}
                                        轮对话</span
                                    >
                                </div>
                                <div
                                    v-if="session.current_script"
                                    class="session-preview"
                                >
                                    {{
                                        session.current_script?.substring(
                                            0,
                                            100,
                                        ) || ""
                                    }}...
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-else-if="entryMode === 'debate'" class="mode-panel">
                        <p class="section-tip">
                            输入题目与主题，自动生成辩论/会议内容，再可直接转音频。
                        </p>
                        <div class="rss-form">
                            <div class="form-group">
                                <label>模式</label>
                                <select
                                    v-model="debateMode"
                                    class="form-select"
                                >
                                    <option value="debate">辩论</option>
                                    <option value="conference">会议</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>标题</label>
                                <input
                                    v-model="debateTitle"
                                    type="text"
                                    class="form-input"
                                    placeholder="例如：AI是否会取代程序员"
                                />
                            </div>
                            <div class="form-group debate-topic">
                                <label>{{
                                    debateMode === "debate" ? "辩题" : "主题"
                                }}</label>
                                <textarea
                                    v-model="debateTopic"
                                    rows="4"
                                    class="form-input"
                                    :placeholder="
                                        debateMode === 'debate'
                                            ? '输入辩题与双方立场'
                                            : '输入会议讨论主题'
                                    "
                                ></textarea>
                            </div>
                            <div class="form-group">
                                <label>轮数</label>
                                <input
                                    v-model.number="debateRounds"
                                    type="number"
                                    min="2"
                                    max="8"
                                    class="form-input"
                                />
                            </div>
                        </div>
                        <p v-if="debateError" class="error-message">
                            {{ debateError }}
                        </p>
                        <div class="rss-actions">
                            <button
                                class="mofa-btn mofa-btn-primary"
                                :disabled="debateSubmitting"
                                @click="createDebateFromStudio"
                            >
                                {{
                                    debateSubmitting
                                        ? "生成中..."
                                        : "生成辩论/会议"
                                }}
                            </button>
                        </div>
                    </div>

                    <div v-else class="mode-panel">
                        <p class="section-tip">
                            贴入 RSS，多源汇总后由 LLM 生成脚本与音频任务。
                        </p>
                        <div class="rss-form">
                            <div class="form-group">
                                <label>RSS 地址（多行可多源）</label>
                                <textarea
                                    v-model="rssUrlsText"
                                    class="form-input"
                                    rows="3"
                                    placeholder="https://news.ycombinator.com/rss&#10;https://example.com/feed.xml"
                                ></textarea>
                            </div>
                            <div class="form-group">
                                <label>标题（可选）</label>
                                <input
                                    v-model="rssTitle"
                                    type="text"
                                    class="form-input"
                                    placeholder="不填则自动命名"
                                />
                            </div>
                            <div class="form-group">
                                <label>模板</label>
                                <select
                                    v-model="rssTemplate"
                                    class="form-select"
                                >
                                    <option value="web_summary">
                                        网页摘要
                                    </option>
                                    <option value="news_flash">新闻快报</option>
                                    <option value="deep_dive">深度长谈</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>条目数</label>
                                <input
                                    v-model.number="rssMaxItems"
                                    type="number"
                                    min="1"
                                    max="20"
                                    class="form-input"
                                />
                            </div>
                            <div class="form-group">
                                <label>排序</label>
                                <select v-model="rssSortBy" class="form-select">
                                    <option value="latest">最新优先</option>
                                    <option value="oldest">最早优先</option>
                                    <option value="title">按标题</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>定时生成（可选）</label>
                                <input
                                    v-model="rssScheduledAtLocal"
                                    type="datetime-local"
                                    class="form-input"
                                />
                            </div>
                            <div class="form-group">
                                <label>关联频道（可选）</label>
                                <select v-model="rssShowId" class="form-select">
                                    <option :value="null">
                                        默认频道（自动）
                                    </option>
                                    <option
                                        v-for="show in myShows"
                                        :key="show.id"
                                        :value="show.id"
                                    >
                                        {{ show.title }}
                                    </option>
                                </select>
                            </div>
                            <div class="speaker-config">
                                <div class="speaker-config-header">
                                    <label>播报角色与音色（可选）</label>
                                    <button
                                        type="button"
                                        class="mofa-btn mofa-btn-sm"
                                        :disabled="voiceCatalogLoading"
                                        @click="loadTTSVoices({ refresh: true, silent: false })"
                                    >
                                        {{ voiceCatalogLoading ? "刷新中..." : "刷新音色" }}
                                    </button>
                                </div>
                                <p v-if="voiceCatalogError" class="hint">{{ voiceCatalogError }}</p>
                                <div class="speaker-grid">
                                    <div class="form-group">
                                        <label>主持人名称</label>
                                        <input
                                            v-model="rssHostName"
                                            type="text"
                                            class="form-input"
                                            placeholder="默认：大牛"
                                        />
                                    </div>
                                    <div class="form-group">
                                        <label>主持人音色</label>
                                        <select v-model="rssHostVoiceId" class="form-select">
                                            <option value="">默认音色（自动）</option>
                                            <option
                                                v-for="voice in availableTTSVoices"
                                                :key="`rss-host-${voice.voice_id}`"
                                                :value="voice.voice_id"
                                            >
                                                {{ formatVoiceLabel(voice) }}
                                            </option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label>嘉宾名称</label>
                                        <input
                                            v-model="rssGuestName"
                                            type="text"
                                            class="form-input"
                                            placeholder="默认：一帆"
                                        />
                                    </div>
                                    <div class="form-group">
                                        <label>嘉宾音色</label>
                                        <select v-model="rssGuestVoiceId" class="form-select">
                                            <option value="">默认音色（自动）</option>
                                            <option
                                                v-for="voice in availableTTSVoices"
                                                :key="`rss-guest-${voice.voice_id}`"
                                                :value="voice.voice_id"
                                            >
                                                {{ formatVoiceLabel(voice) }}
                                            </option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <label class="rss-checkbox">
                                <input
                                    v-model="rssDeduplicate"
                                    type="checkbox"
                                />
                                去重（按标题+链接）
                            </label>
                        </div>
                        <p v-if="rssError" class="error-message">
                            {{ rssError }}
                        </p>
                        <div class="rss-actions">
                            <button
                                class="mofa-btn"
                                :disabled="rssSubmitting"
                                @click="previewRSSScript"
                            >
                                {{ rssSubmitting ? "处理中..." : "预览脚本" }}
                            </button>
                            <button
                                class="mofa-btn mofa-btn-success"
                                :disabled="rssSubmitting"
                                @click="generateFromRSS"
                            >
                                {{ rssSubmitting ? "提交中..." : "生成音频" }}
                            </button>
                        </div>
                        <div v-if="rssScriptPreview" class="rss-script-editor">
                            <label class="form-group-label">脚本（可编辑）</label>
                            <textarea
                                v-model="rssScriptDraft"
                                class="form-input rss-script-textarea"
                                rows="12"
                                placeholder="预览后可在此修改脚本，再提交生成音频"
                            ></textarea>
                            <p class="hint">提示：你可直接改文案与节奏，提交时将按此稿生成。</p>
                        </div>
                    </div>
                </div>

                <div class="generation-section mofa-card">
                    <div class="section-header">
                        <h2>生成记录</h2>
                        <button
                            class="mofa-btn mofa-btn-sm"
                            @click="loadGenerationQueue"
                        >
                            刷新
                        </button>
                    </div>
                    <!-- 筛选控件已隐藏，显示所有任务 -->
                    <div v-if="queueLoading" class="loading-state small">
                        加载中...
                    </div>
                    <div
                        v-else-if="generationQueue.length === 0"
                        class="empty-state small"
                    >
                        <p>暂无生成任务</p>
                        <p class="hint">完成脚本或填写表单后，即可提交任务。</p>
                    </div>
                    <div v-else class="generation-list">
                        <div
                            v-for="episode in generationQueue"
                            :key="episode.id"
                            class="generation-item"
                            @click="openGenerationItem(episode)"
                        >
                            <div class="generation-info">
                                <div class="generation-title">
                                    {{ episode.title }}
                                </div>
                                <div class="generation-meta">
                                    <span>{{
                                        episode.show?.title ||
                                        "默认频道（自动）"
                                    }}</span>
                                    <span
                                        >提交于
                                        {{
                                            formatTime(episode.created_at)
                                        }}</span
                                    >
                                </div>
                                <div class="generation-stage-row">
                                    <span class="generation-stage-text">{{
                                        formatStage(episode)
                                    }}</span>
                                    <span class="generation-stage-percent"
                                        >{{
                                            generationProgress(episode)
                                        }}%</span
                                    >
                                </div>
                                <div class="generation-stage-progress">
                                    <div
                                        class="generation-stage-progress-bar"
                                        :style="{
                                            width: `${generationProgress(episode)}%`,
                                        }"
                                    ></div>
                                </div>
                                <div
                                    v-if="episode.generation_error"
                                    class="generation-error"
                                >
                                    {{ episode.generation_error }}
                                </div>
                            </div>
                            <div class="generation-actions">
                                <span :class="statusClass(episode.status)">{{
                                    formatStatus(episode.status)
                                }}</span>
                                <button
                                    v-if="canManageCover(episode)"
                                    class="queue-action"
                                    @click.stop="openCoverDialog(episode)"
                                >
                                    封面
                                </button>
                                <button
                                    v-if="canCancelEpisode(episode)"
                                    class="queue-action queue-action-cancel"
                                    @click.stop="cancelGeneration(episode)"
                                >
                                    取消
                                </button>
                                <button
                                    v-if="canRetryEpisode(episode)"
                                    class="queue-action queue-action-retry"
                                    @click.stop="retryGeneration(episode)"
                                >
                                    重试
                                </button>
                                <button
                                    v-if="canDeleteEpisode(episode)"
                                    class="queue-action"
                                    @click.stop="deleteGeneration(episode)"
                                >
                                    删除
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 创作工作区 -->
            <div v-else class="studio-workspace">
                <div class="workspace-header">
                    <div class="header-left">
                        <button @click="backToList" class="mofa-btn">
                            返回列表
                        </button>
                        <div class="title-block">
                            <h2 class="workspace-title">
                                {{ currentSession.title }}
                            </h2>
                            <div v-if="sessionMeta" class="workspace-meta">
                                <span class="meta-item">
                                    <span class="label">关联频道：</span
                                    >{{ sessionMeta.showTitle }}
                                </span>
                                <span class="meta-item">
                                    <span class="label">对话：</span
                                    >{{
                                        sessionMeta.messageCount.toLocaleString(
                                            "zh-CN",
                                        )
                                    }}
                                    条
                                </span>
                                <span class="meta-item">
                                    <span class="label">文件：</span
                                    >{{
                                        sessionMeta.fileCount.toLocaleString(
                                            "zh-CN",
                                        )
                                    }}
                                    个
                                </span>
                                <span class="meta-item">
                                    <span class="label">更新：</span
                                    >{{
                                        sessionMeta.updatedAt
                                            ? formatTime(sessionMeta.updatedAt)
                                            : "刚刚"
                                    }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="workspace-actions">
                        <button
                            class="mofa-btn delete-session-btn"
                            @click="confirmDeleteSession(currentSession.id)"
                            :disabled="generating"
                        >
                            删除会话
                        </button>
                        <button
                            v-if="currentSession.current_script"
                            @click="openGenerateDialog"
                            class="mofa-btn mofa-btn-success"
                            :disabled="generating"
                        >
                            {{ generating ? "生成中..." : "生成音频" }}
                        </button>
                    </div>
                </div>

                <div class="workspace-content">
                    <!-- 左侧：对话区 -->
                    <div class="chat-panel mofa-card">
                        <div class="panel-header">
                            <h3>对话</h3>
                            <div class="header-actions">
                                <TrendingPanel
                                    @select-trending="handleTrendingSelect"
                                />
                                <button
                                    @click="showUploadDialog = true"
                                    class="mofa-btn mofa-btn-sm"
                                >
                                    上传参考文件
                                </button>
                            </div>
                        </div>

                        <!-- 参考文件列表 -->
                        <div
                            v-if="currentSession.uploaded_files?.length > 0"
                            class="reference-files"
                        >
                            <div class="files-header">
                                参考文件 ({{
                                    currentSession.uploaded_files.length
                                }})
                            </div>
                            <div class="files-list">
                                <div
                                    v-for="file in currentSession.uploaded_files"
                                    :key="file.id"
                                    class="file-item"
                                >
                                    <span class="file-name">{{
                                        file.original_filename
                                    }}</span>
                                    <span class="file-size">{{
                                        formatFileSize(file.file_size)
                                    }}</span>
                                    <button
                                        @click="deleteFile(file.id)"
                                        class="btn-delete"
                                    >
                                        删除
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 对话消息 -->
                        <div ref="chatMessages" class="chat-messages">
                            <div
                                v-if="
                                    !currentSession.chat_history ||
                                    currentSession.chat_history.length === 0
                                "
                                class="chat-welcome"
                            >
                                <p>开始与 AI 对话，创作你的音频脚本</p>
                                <ul>
                                    <li>告诉我你想创作的主题与风格</li>
                                    <li>
                                        上传参考文件（支持 txt/pdf/md/docx）
                                    </li>
                                    <li>让我帮你生成或修改脚本</li>
                                </ul>
                            </div>

                            <div
                                v-for="(
                                    msg, index
                                ) in currentSession.chat_history"
                                :key="index"
                                class="message"
                                :class="[
                                    msg.role,
                                    {
                                        typing: msg.typing,
                                        system: msg.system,
                                        pending: msg.pending,
                                    },
                                ]"
                            >
                                <div class="message-role">
                                    {{ msg.role === "user" ? "你" : "AI" }}
                                </div>
                                <div class="message-content">
                                    <div
                                        v-if="msg.typing"
                                        class="thinking-indicator"
                                    >
                                        <span class="dot"></span>
                                        <span class="dot"></span>
                                        <span class="dot"></span>
                                    </div>
                                    <div
                                        v-else
                                        class="message-text"
                                        v-html="formatMessage(msg.content)"
                                    ></div>
                                    <div
                                        v-if="!msg.typing && msg.timestamp"
                                        class="message-time"
                                    >
                                        {{ formatTime(msg.timestamp) }}
                                    </div>
                                    <div
                                        v-if="msg.pending && !msg.typing"
                                        class="message-status"
                                    >
                                        等待 AI 回复...
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 输入框 -->
                        <div class="chat-input">
                            <textarea
                                v-model="userMessage"
                                @keydown.ctrl.enter="sendMessage"
                                placeholder="输入你的想法... (Ctrl+Enter 发送)"
                                rows="3"
                            ></textarea>
                            <button
                                @click="sendMessage"
                                class="mofa-btn mofa-btn-primary"
                                :disabled="!userMessage.trim() || aiThinking"
                            >
                                {{ aiThinking ? "AI 回复中..." : "发送" }}
                            </button>
                        </div>
                    </div>

                    <!-- 右侧：脚本预览 -->
                    <div class="script-panel mofa-card">
                        <div class="panel-header">
                            <h3>脚本预览</h3>
                            <div class="panel-actions">
                                <button
                                    v-if="!isEditingScript"
                                    @click="startEditScript"
                                    class="mofa-btn mofa-btn-sm"
                                >
                                    编辑
                                </button>
                                <button
                                    v-if="isEditingScript"
                                    @click="saveScriptEdit"
                                    class="mofa-btn mofa-btn-sm mofa-btn-success"
                                >
                                    保存
                                </button>
                                <button
                                    v-if="isEditingScript"
                                    @click="cancelScriptEdit"
                                    class="mofa-btn mofa-btn-sm"
                                >
                                    取消
                                </button>
                                <button
                                    v-if="
                                        currentSession.current_script &&
                                        !isEditingScript
                                    "
                                    @click="copyScript"
                                    class="mofa-btn mofa-btn-sm"
                                >
                                    复制
                                </button>
                            </div>
                        </div>

                        <div v-if="scriptMeta" class="script-meta">
                            <span class="meta-item">
                                <span class="label">字数：</span
                                >{{ scriptMeta.words.toLocaleString("zh-CN") }}
                            </span>
                            <span class="meta-item">
                                <span class="label">字符：</span
                                >{{
                                    scriptMeta.characters.toLocaleString(
                                        "zh-CN",
                                    )
                                }}
                            </span>
                            <span class="meta-item">
                                <span class="label">更新：</span
                                >{{
                                    scriptMeta.lastUpdated
                                        ? formatTime(scriptMeta.lastUpdated)
                                        : "刚刚"
                                }}
                            </span>
                        </div>

                        <div class="script-content">
                            <textarea
                                v-if="isEditingScript"
                                v-model="editableScript"
                                class="script-editor"
                                placeholder="在这里编辑脚本，可以直接粘贴外部内容..."
                            ></textarea>
                            <div
                                v-else-if="!currentSession.current_script"
                                class="script-empty"
                            >
                                <p>还没有生成脚本</p>
                                <p class="hint">
                                    点击"编辑"按钮直接粘贴内容，或在左侧与 AI 对话创作
                                </p>
                            </div>
                            <pre v-else class="script-text">{{
                                currentSession.current_script
                            }}</pre>
                        </div>

                        <div
                            v-if="!isEditingScript && scriptSegments.length > 0"
                            class="segment-tools"
                        >
                            <div class="segment-tools-header">
                                <h4>试听即改</h4>
                                <span class="hint"
                                    >段落级试听 / 局部重写 / 局部重生音频</span
                                >
                            </div>
                            <div class="segment-controls">
                                <select
                                    v-model.number="selectedSegmentIndex"
                                    class="form-select"
                                >
                                    <option
                                        v-for="segment in scriptSegments"
                                        :key="segment.index"
                                        :value="segment.index"
                                    >
                                        段 {{ segment.index + 1 }} ·
                                        {{ segment.role }}
                                    </option>
                                </select>
                                <button
                                    class="mofa-btn mofa-btn-sm"
                                    :disabled="
                                        segmentPreviewLoading ||
                                        !selectedSegment
                                    "
                                    @click="previewSelectedSegment"
                                >
                                    {{
                                        segmentPreviewLoading
                                            ? "生成中..."
                                            : "试听片段"
                                    }}
                                </button>
                                <button
                                    class="mofa-btn mofa-btn-sm mofa-btn-success"
                                    :disabled="
                                        segmentRewriteLoading ||
                                        !selectedSegment ||
                                        !segmentRewriteInstruction.trim()
                                    "
                                    @click="rewriteSelectedSegment"
                                >
                                    {{
                                        segmentRewriteLoading
                                            ? "改写中..."
                                            : "局部重写"
                                    }}
                                </button>
                            </div>
                            <div
                                v-if="selectedSegment"
                                class="segment-selected"
                            >
                                <div class="segment-label">当前片段</div>
                                <pre class="script-text">{{
                                    selectedSegment.raw
                                }}</pre>
                            </div>
                            <textarea
                                v-model="segmentRewriteInstruction"
                                class="segment-instruction"
                                placeholder="改写要求：例如 更口语、更短、保留核心观点"
                            ></textarea>
                            <audio
                                v-if="segmentPreviewUrl"
                                :src="segmentPreviewUrl"
                                controls
                                class="segment-audio"
                            ></audio>
                        </div>

                        <div
                            v-if="currentSession.script_versions?.length > 1"
                            class="script-versions"
                        >
                            <div class="versions-header">
                                历史版本 ({{
                                    currentSession.script_versions.length
                                }})
                            </div>
                            <div class="versions-list">
                                <button
                                    v-for="(
                                        version, index
                                    ) in currentSession.script_versions
                                        .slice()
                                        .reverse()"
                                    :key="index"
                                    @click="viewVersion(version)"
                                    class="version-item"
                                >
                                    版本
                                    {{
                                        currentSession.script_versions.length -
                                        index
                                    }}
                                    - {{ formatTime(version.created_at) }}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 上传文件对话框 -->
            <div
                v-if="showUploadDialog"
                class="modal-overlay"
                @click.self="showUploadDialog = false"
            >
                <div class="modal-content mofa-card">
                    <div class="modal-header">
                        <h3>上传参考文件</h3>
                        <button
                            @click="showUploadDialog = false"
                            class="btn-close"
                        >
                            ×
                        </button>
                    </div>
                    <div class="modal-body">
                        <p>支持格式：txt, pdf, md, docx（最大 10MB）</p>
                        <input
                            ref="fileInput"
                            type="file"
                            @change="handleFileSelect"
                            accept=".txt,.pdf,.md,.docx"
                            class="file-input"
                        />
                        <div v-if="uploadProgress > 0" class="upload-progress">
                            <div
                                class="progress-bar"
                                :style="{ width: uploadProgress + '%' }"
                            ></div>
                            <span>{{ uploadProgress }}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 生成音频对话框 -->
            <div
                v-if="showGenerateDialog"
                class="modal-overlay"
                @click.self="closeGenerateDialog"
            >
                <div class="modal-content mofa-card">
                    <div class="modal-header">
                        <h3>生成音频</h3>
                        <button @click="closeGenerateDialog" class="btn-close">
                            ×
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>音频标题</label>
                            <input
                                v-model="generateTitle"
                                type="text"
                                placeholder="请输入生成标题"
                                class="form-input"
                            />
                        </div>
                        <div class="form-group">
                            <label>关联频道（可选）</label>
                            <select
                                v-model="generateShowId"
                                class="form-select"
                            >
                                <option :value="null">默认频道（自动）</option>
                                <option
                                    v-for="show in availableShows"
                                    :key="show.id"
                                    :value="show.id"
                                >
                                    {{ show.title }}
                                </option>
                            </select>
                        </div>
                        <div class="speaker-config">
                            <div class="speaker-config-header">
                                <label>播报角色与音色（可选）</label>
                                <button
                                    type="button"
                                    class="mofa-btn mofa-btn-sm"
                                    :disabled="voiceCatalogLoading"
                                    @click="loadTTSVoices({ refresh: true, silent: false })"
                                >
                                    {{ voiceCatalogLoading ? "刷新中..." : "刷新音色" }}
                                </button>
                            </div>
                            <p v-if="voiceCatalogError" class="hint">{{ voiceCatalogError }}</p>
                            <div class="speaker-grid">
                                <div class="form-group">
                                    <label>主持人名称</label>
                                    <input
                                        v-model="generateHostName"
                                        type="text"
                                        class="form-input"
                                        placeholder="默认：大牛"
                                    />
                                </div>
                                <div class="form-group">
                                    <label>主持人音色</label>
                                    <select v-model="generateHostVoiceId" class="form-select">
                                        <option value="">默认音色（自动）</option>
                                        <option
                                            v-for="voice in availableTTSVoices"
                                            :key="`generate-host-${voice.voice_id}`"
                                            :value="voice.voice_id"
                                        >
                                            {{ formatVoiceLabel(voice) }}
                                        </option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>嘉宾名称</label>
                                    <input
                                        v-model="generateGuestName"
                                        type="text"
                                        class="form-input"
                                        placeholder="默认：一帆"
                                    />
                                </div>
                                <div class="form-group">
                                    <label>嘉宾音色</label>
                                    <select v-model="generateGuestVoiceId" class="form-select">
                                        <option value="">默认音色（自动）</option>
                                        <option
                                            v-for="voice in availableTTSVoices"
                                            :key="`generate-guest-${voice.voice_id}`"
                                            :value="voice.voice_id"
                                        >
                                            {{ formatVoiceLabel(voice) }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <p v-if="availableShows.length === 0" class="hint">
                            暂无已建频道，系统会自动使用默认频道。
                        </p>
                        <p v-if="generateError" class="error-message">
                            {{ generateError }}
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button @click="closeGenerateDialog" class="mofa-btn">
                            取消
                        </button>
                        <button
                            @click="confirmGeneratePodcast"
                            class="mofa-btn mofa-btn-success"
                            :disabled="generating || !generateTitle.trim()"
                        >
                            {{ generating ? "提交中..." : "生成" }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- 新建会话对话框 -->
            <div
                v-if="showNewSessionDialog"
                class="modal-overlay"
                @click.self="showNewSessionDialog = false"
            >
                <div class="modal-content mofa-card">
                    <div class="modal-header">
                        <h3>新建脚本创作会话</h3>
                        <button
                            @click="showNewSessionDialog = false"
                            class="btn-close"
                        >
                            ×
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>会话标题</label>
                            <input
                                v-model="newSessionTitle"
                                type="text"
                                placeholder="例如：第一期 - 人工智能简介"
                                class="form-input"
                            />
                        </div>
                        <div class="form-group">
                            <label>关联频道（可选）</label>
                            <select
                                v-model="newSessionShowId"
                                class="form-select"
                            >
                                <option :value="null">默认频道（自动）</option>
                                <option
                                    v-for="show in myShows"
                                    :key="show.id"
                                    :value="show.id"
                                >
                                    {{ show.title }}
                                </option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button
                            @click="showNewSessionDialog = false"
                            class="mofa-btn"
                        >
                            取消
                        </button>
                        <button
                            @click="confirmCreateSession"
                            class="mofa-btn mofa-btn-primary"
                            :disabled="!newSessionTitle.trim()"
                        >
                            创建
                        </button>
                    </div>
                </div>
            </div>

            <!-- 封面候选图对话框 -->
            <div
                v-if="showCoverDialog"
                class="modal-overlay"
                @click.self="closeCoverDialog"
            >
                <div class="modal-content mofa-card cover-modal">
                    <div class="modal-header">
                        <h3>封面候选图</h3>
                        <button @click="closeCoverDialog" class="btn-close">
                            ×
                        </button>
                    </div>
                    <div class="modal-body">
                        <p v-if="coverTargetEpisode" class="hint">
                            目标单集：{{ coverTargetEpisode.title }}
                        </p>
                        <div class="cover-toolbar">
                            <button
                                class="mofa-btn mofa-btn-sm"
                                :disabled="coverLoading"
                                @click="loadCoverCandidates"
                            >
                                {{ coverLoading ? "生成中..." : "重抽 4 张" }}
                            </button>
                        </div>
                        <p v-if="coverError" class="error-message">
                            {{ coverError }}
                        </p>
                        <div v-if="coverLoading" class="loading-state small">
                            封面生成中...
                        </div>
                        <div
                            v-else-if="coverCandidates.length === 0"
                            class="empty-state small"
                        >
                            <p>暂无候选图，请点击“重抽 4 张”</p>
                        </div>
                        <div v-else class="cover-grid">
                            <div
                                v-for="candidate in coverCandidates"
                                :key="candidate.path"
                                class="cover-item"
                            >
                                <img
                                    :src="candidate.url"
                                    alt="cover candidate"
                                    class="cover-image"
                                />
                                <button
                                    class="mofa-btn mofa-btn-sm mofa-btn-success"
                                    :disabled="coverApplying"
                                    @click="applyCoverCandidate(candidate)"
                                >
                                    {{
                                        coverApplying ? "应用中..." : "使用此图"
                                    }}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 历史版本查看对话框 -->
            <div
                v-if="showVersionDialog && viewingVersion"
                class="modal-overlay"
                @click.self="showVersionDialog = false"
            >
                <div class="modal-content mofa-card version-modal">
                    <div class="modal-header">
                        <h3>脚本版本 {{ viewingVersion.version }}</h3>
                        <button
                            @click="showVersionDialog = false"
                            class="btn-close"
                        >
                            ×
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="version-meta">
                            <span
                                >创建时间：{{
                                    formatTime(viewingVersion.timestamp)
                                }}</span
                            >
                            <span
                                >字数：{{
                                    viewingVersion.script?.length || 0
                                }}</span
                            >
                        </div>
                        <div class="version-script-content">
                            <pre class="script-text">{{
                                viewingVersion.script
                            }}</pre>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button
                            @click="showVersionDialog = false"
                            class="mofa-btn"
                        >
                            关闭
                        </button>
                        <button
                            @click="restoreVersion(viewingVersion)"
                            class="mofa-btn mofa-btn-primary"
                        >
                            恢复此版本
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import podcastsAPI from "@/api/podcasts";
import { ElMessage, ElMessageBox } from "element-plus";
import TrendingPanel from "@/components/creator/TrendingPanel.vue";

const router = useRouter();

// 状态
const loading = ref(false);
const sessions = ref([]);
const currentSession = ref(null);
const myShows = ref([]);
const entryMode = ref("dialogue");
const generationQueue = ref([]);
const queueLoading = ref(false);
const queueFilters = ref([]); // 空数组表示显示所有状态的任务

// 聊天相关
const userMessage = ref("");
const aiThinking = ref(false);
const chatMessages = ref(null);

// 脚本编辑相关
const isEditingScript = ref(false);
const editableScript = ref("");

const sessionMeta = computed(() => {
    const session = currentSession.value;
    if (!session) return null;

    return {
        showTitle: session.show?.title || "默认频道（自动）",
        messageCount: session.chat_history?.length || 0,
        fileCount:
            session.uploaded_files_count ?? session.uploaded_files?.length ?? 0,
        updatedAt: session.updated_at,
    };
});

const scriptMeta = computed(() => {
    const session = currentSession.value;
    if (!session?.current_script) return null;

    const plain = session.current_script.trim();
    const wordCount = plain ? plain.replace(/\s+/g, " ").split(" ").length : 0;

    return {
        characters: plain.length,
        words: wordCount,
        lastUpdated: session.updated_at,
    };
});

const selectedSegmentIndex = ref(0);
const segmentPreviewLoading = ref(false);
const segmentRewriteLoading = ref(false);
const segmentPreviewUrl = ref("");
const segmentRewriteInstruction = ref("");

function parseScriptSegments(script) {
    if (!script) return [];
    const matches = script.match(/【[^】]+】[\s\S]*?(?=【[^】]+】|$)/g) || [];
    return matches
        .map((raw, index) => {
            const roleMatch = raw.match(/^【([^】]+)】/);
            return {
                index,
                raw: raw.trim(),
                role: roleMatch?.[1] || "未知角色",
            };
        })
        .filter((item) => item.raw);
}

const scriptSegments = computed(() =>
    parseScriptSegments(currentSession.value?.current_script || ""),
);

const selectedSegment = computed(() => {
    if (!scriptSegments.value.length) return null;
    const maxIndex = scriptSegments.value.length - 1;
    const index = Math.max(0, Math.min(selectedSegmentIndex.value, maxIndex));
    if (index !== selectedSegmentIndex.value) {
        selectedSegmentIndex.value = index;
    }
    return scriptSegments.value[index];
});

const availableShows = computed(() => {
    const shows = Array.isArray(myShows.value) ? [...myShows.value] : [];
    const currentShow = currentSession.value?.show;
    if (currentShow && !shows.some((show) => show.id === currentShow.id)) {
        shows.push(currentShow);
    }
    return shows;
});

const generationStatusOptions = [
    { code: "processing", label: "生成中" },
    { code: "failed", label: "失败" },
    { code: "published", label: "已完成" },
];

// 上传相关
const showUploadDialog = ref(false);
const uploadProgress = ref(0);
const fileInput = ref(null);

// 生成音频
const generating = ref(false);
const showGenerateDialog = ref(false);
const generateTitle = ref("");
const generateShowId = ref(null);
const generateError = ref("");
const DEFAULT_HOST_NAME = "大牛";
const DEFAULT_GUEST_NAME = "一帆";
const generateHostName = ref(DEFAULT_HOST_NAME);
const generateGuestName = ref(DEFAULT_GUEST_NAME);
const generateHostVoiceId = ref("");
const generateGuestVoiceId = ref("");
const voiceCatalogLoading = ref(false);
const voiceCatalogError = ref("");
const ttsVoices = ref([]);

// 新建会话
const showNewSessionDialog = ref(false);
const newSessionTitle = ref("");
const newSessionShowId = ref(null);

// 历史版本查看
const showVersionDialog = ref(false);
const viewingVersion = ref(null);

// 封面候选图
const showCoverDialog = ref(false);
const coverTargetEpisode = ref(null);
const coverCandidates = ref([]);
const coverLoading = ref(false);
const coverApplying = ref(false);
const coverError = ref("");

// RSS 快速生成
const rssUrlsText = ref("https://news.ycombinator.com/rss");
const rssShowId = ref(null);
const rssTitle = ref("");
const rssTemplate = ref("news_flash");
const rssMaxItems = ref(2);
const rssDeduplicate = ref(true);
const rssSortBy = ref("latest");
const rssScheduledAtLocal = ref("");
const rssSubmitting = ref(false);
const rssError = ref("");
const rssScriptPreview = ref("");
const rssScriptDraft = ref("");
const rssHostName = ref(DEFAULT_HOST_NAME);
const rssGuestName = ref(DEFAULT_GUEST_NAME);
const rssHostVoiceId = ref("");
const rssGuestVoiceId = ref("");
const debateMode = ref("debate");
const debateTitle = ref("");
const debateTopic = ref("");
const debateRounds = ref(3);
const debateSubmitting = ref(false);
const debateError = ref("");

const fallbackVoices = [
    { voice_id: "ttv-voice-2025103011222725-sg8dZxUP", voice_name: "大牛（默认）", language: "zh" },
    { voice_id: "moss_audio_aaa1346a-7ce7-11f0-8e61-2e6e3c7ee85d", voice_name: "一帆（默认）", language: "zh" },
];

const availableTTSVoices = computed(() => {
    const voices = Array.isArray(ttsVoices.value) && ttsVoices.value.length
        ? ttsVoices.value
        : fallbackVoices;
    return voices.filter((voice) => voice?.voice_id);
});

function formatVoiceLabel(voice) {
    if (!voice) return "";
    const voiceName = voice.voice_name || voice.voice_id;
    const tags = [];
    if (voice.language) {
        tags.push(voice.language.toUpperCase());
    }
    if (voice.source === "legacy_default") {
        tags.push("默认");
    }
    return tags.length ? `${voiceName}（${tags.join(" · ")}）` : voiceName;
}

async function loadTTSVoices(options = {}) {
    const { refresh = false, silent = true } = options;
    voiceCatalogLoading.value = true;
    voiceCatalogError.value = "";
    try {
        const data = await podcastsAPI.getTTSVoices({
            language: "zh",
            refresh: refresh ? 1 : undefined,
        });
        ttsVoices.value = Array.isArray(data?.voices) ? data.voices : [];
        if (!silent) {
            ElMessage.success(`已载入 ${ttsVoices.value.length} 个音色`);
        }
    } catch (error) {
        voiceCatalogError.value =
            error.response?.data?.error || error.message || "音色加载失败，已回退默认音色";
        if (!silent) {
            ElMessage.warning(voiceCatalogError.value);
        }
    } finally {
        voiceCatalogLoading.value = false;
    }
}

function applySpeakerPayload(payload, options = {}) {
    const hostName = (options.hostName || "").trim() || DEFAULT_HOST_NAME;
    const guestName = (options.guestName || "").trim() || DEFAULT_GUEST_NAME;
    const hostVoiceId = (options.hostVoiceId || "").trim();
    const guestVoiceId = (options.guestVoiceId || "").trim();

    payload.host_name = hostName;
    payload.guest_name = guestName;
    if (hostVoiceId) {
        payload.host_voice_id = hostVoiceId;
    }
    if (guestVoiceId) {
        payload.guest_voice_id = guestVoiceId;
    }
    return payload;
}

// 加载会话列表
async function loadSessions() {
    loading.value = true;
    try {
        const data = await podcastsAPI.getScriptSessions();
        // 兼容分页和非分页两种响应格式
        sessions.value = Array.isArray(data) ? data : data.results || [];
    } catch (error) {
        console.error("加载会话失败:", error);
        ElMessage.error("加载会话失败，请稍后重试");
    } finally {
        loading.value = false;
    }
}

async function loadGenerationQueue() {
    queueLoading.value = true;
    try {
        const params = queueFilters.value.length
            ? { status: queueFilters.value.join(",") }
            : {};
        const data = await podcastsAPI.getGenerationQueue(params);
        const list = Array.isArray(data) ? data : data.results || [];
        if (queueFilters.value.includes("published")) {
            generationQueue.value = list.filter((episode) => {
                if (episode.status !== "published") return true;
                const desc = episode.description || "";
                const filePath = episode.audio_file || "";
                return (
                    desc.includes("AI Generated Podcast") ||
                    filePath.includes("generated_")
                );
            });
        } else {
            generationQueue.value = list;
        }
    } catch (error) {
        console.error("加载生成记录失败:", error);
    } finally {
        queueLoading.value = false;
    }
}

// 加载我的音频
async function loadMyShows() {
    try {
        const data = await podcastsAPI.getMyShows();
        myShows.value = Array.isArray(data) ? data : data.results || [];
    } catch (error) {
        console.error("加载节目失败:", error);
    }
}

async function previewRSSScript() {
    const urls = parseRssUrls();
    if (!urls.length) {
        rssError.value = "请填写 RSS 地址";
        return;
    }
    rssSubmitting.value = true;
    rssError.value = "";
    try {
        const payload = {
            rss_urls: urls,
            template: rssTemplate.value,
            max_items: Number(rssMaxItems.value) || 2,
            deduplicate: rssDeduplicate.value,
            sort_by: rssSortBy.value,
            dry_run: true,
        };
        applySpeakerPayload(payload, {
            hostName: rssHostName.value,
            guestName: rssGuestName.value,
            hostVoiceId: rssHostVoiceId.value,
            guestVoiceId: rssGuestVoiceId.value,
        });
        if (rssShowId.value) {
            payload.show_id = Number(rssShowId.value);
        }
        const data = await podcastsAPI.generateEpisodeFromRSS(payload);
        rssScriptPreview.value = data.script || "";
        rssScriptDraft.value = data.script || "";
        ElMessage.success(`已解析 ${data.item_count || 0} 条并生成脚本`);
    } catch (error) {
        rssError.value =
            error.response?.data?.error || error.message || "预览失败";
    } finally {
        rssSubmitting.value = false;
    }
}

async function generateFromRSS() {
    const urls = parseRssUrls();
    if (!urls.length) {
        rssError.value = "请填写 RSS 地址";
        return;
    }
    rssSubmitting.value = true;
    rssError.value = "";
    try {
        const payload = {
            rss_urls: urls,
            title: rssTitle.value.trim() || undefined,
            template: rssTemplate.value,
            max_items: Number(rssMaxItems.value) || 2,
            deduplicate: rssDeduplicate.value,
            sort_by: rssSortBy.value,
            scheduled_at: normalizeScheduledAt(rssScheduledAtLocal.value),
            dry_run: false,
        };
        const manualScript = rssScriptDraft.value.trim();
        if (manualScript) {
            payload.script = manualScript;
        }
        applySpeakerPayload(payload, {
            hostName: rssHostName.value,
            guestName: rssGuestName.value,
            hostVoiceId: rssHostVoiceId.value,
            guestVoiceId: rssGuestVoiceId.value,
        });
        if (rssShowId.value) {
            payload.show_id = Number(rssShowId.value);
        }
        await podcastsAPI.generateEpisodeFromRSS(payload);
        ElMessage.success(
            rssScheduledAtLocal.value
                ? "RSS 定时任务已提交"
                : "RSS 生成任务已提交",
        );
        await loadGenerationQueue();
    } catch (error) {
        rssError.value =
            error.response?.data?.error || error.message || "提交失败";
    } finally {
        rssSubmitting.value = false;
    }
}

async function createDebateFromStudio() {
    if (!debateTitle.value.trim() || !debateTopic.value.trim()) {
        debateError.value = "请填写标题与主题";
        return;
    }

    debateSubmitting.value = true;
    debateError.value = "";
    try {
        const data = await podcastsAPI.generateDebate({
            title: debateTitle.value.trim(),
            topic: debateTopic.value.trim(),
            mode: debateMode.value,
            rounds: Number(debateRounds.value) || 3,
        });

        ElMessage.success("辩论/会议任务已创建");
        debateTitle.value = "";
        debateTopic.value = "";
        if (data?.episode_id) {
            router.push({
                name: "debate-viewer",
                params: { episodeId: data.episode_id },
            });
        }
    } catch (error) {
        debateError.value =
            error.response?.data?.error || error.message || "提交失败";
    } finally {
        debateSubmitting.value = false;
    }
}

function parseRssUrls() {
    return (rssUrlsText.value || "")
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean);
}

function normalizeScheduledAt(value) {
    if (!value) return undefined;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return undefined;
    return date.toISOString();
}

// 创建新会话
function createNewSession() {
    newSessionTitle.value = "";
    newSessionShowId.value = null;
    showNewSessionDialog.value = true;
}

async function confirmCreateSession() {
    if (!newSessionTitle.value.trim()) return;

    try {
        const session = await podcastsAPI.createScriptSession({
            title: newSessionTitle.value,
            show_id: newSessionShowId.value,
        });

        // 确保有基本字段
        if (!session.chat_history) session.chat_history = [];
        if (!session.uploaded_files) session.uploaded_files = [];

        showNewSessionDialog.value = false;
        currentSession.value = session;
        await nextTick();
    } catch (error) {
        console.error("创建会话失败:", error);
        ElMessage.error("创建会话失败，请稍后重试");
    }
}

// 加载会话
async function loadSession(sessionId) {
    try {
        const session = await podcastsAPI.getScriptSession(sessionId);
        currentSession.value = session;
        selectedSegmentIndex.value = 0;
        segmentPreviewUrl.value = "";
        segmentRewriteInstruction.value = "";
        await nextTick();
        scrollToBottom();
    } catch (error) {
        console.error("加载会话失败:", error);
        ElMessage.error("加载会话失败，请稍后重试");
    }
}

// 返回列表
function backToList() {
    currentSession.value = null;
    segmentPreviewUrl.value = "";
    segmentRewriteInstruction.value = "";
    loadSessions();
    loadGenerationQueue();
}

// 删除会话
async function confirmDeleteSession(sessionId) {
    if (!sessionId) return;

    try {
        await ElMessageBox.confirm(
            "确定要删除这个会话吗？删除后无法恢复。",
            "删除会话",
            {
                type: "warning",
                confirmButtonText: "删除",
                cancelButtonText: "取消",
            },
        );

        await podcastsAPI.deleteScriptSession(sessionId);

        if (currentSession.value?.id === sessionId) {
            currentSession.value = null;
        }

        await loadSessions();
        await loadGenerationQueue();
        ElMessage.success("会话已删除");
    } catch (error) {
        if (error !== "cancel") {
            console.error("删除会话失败:", error);
            ElMessage.error("删除会话失败，请稍后重试");
        }
    }
}

function canCancelEpisode(episode) {
    return episode?.status === "processing";
}

function canDeleteEpisode(episode) {
    return episode?.status === "failed";
}

function canRetryEpisode(episode) {
    return episode?.status === "failed";
}

function canManageCover(episode) {
    // 封面按钮已隐藏
    return false;
}

function openGenerationItem(episode) {
    if (!episode?.show?.slug) {
        if (episode?.mode === "debate" || episode?.mode === "conference") {
            router.push({
                name: "debate-viewer",
                params: { episodeId: episode.id },
            });
            return;
        }
        ElMessage.warning("暂时无法跳转，缺少频道信息");
        return;
    }
    router.push({
        name: "manage-show",
        params: { slug: episode.show.slug },
        query: { highlightEpisode: episode.slug },
    });
}

async function cancelGeneration(episode) {
    if (!episode?.id) return;
    try {
        await ElMessageBox.confirm("确定要取消该生成任务吗？", "取消生成", {
            type: "warning",
            confirmButtonText: "取消任务",
            cancelButtonText: "暂不",
        });
    } catch {
        return;
    }

    try {
        await podcastsAPI.deleteEpisode(episode.id);
        await loadGenerationQueue();
    } catch (error) {
        console.error("取消生成任务失败:", error);
        ElMessage.error("取消失败，请稍后再试");
    }
}

async function deleteGeneration(episode) {
    if (!episode?.id) return;
    try {
        await ElMessageBox.confirm("确认删除这条记录？", "删除确认", {
            type: "warning",
            confirmButtonText: "删除",
            cancelButtonText: "取消",
        });
    } catch {
        return;
    }

    try {
        await podcastsAPI.deleteEpisode(episode.id);
        await loadGenerationQueue();
    } catch (error) {
        console.error("删除记录失败:", error);
        ElMessage.error("删除失败，请稍后再试");
    }
}

async function retryGeneration(episode) {
    if (!episode?.id) return;
    try {
        await podcastsAPI.retryEpisodeGeneration(episode.id);
        ElMessage.success("重试任务已提交");
        await loadGenerationQueue();
    } catch (error) {
        console.error("重试任务失败:", error);
        ElMessage.error("重试失败，请稍后再试");
    }
}

function openCoverDialog(episode) {
    coverTargetEpisode.value = episode;
    coverCandidates.value = [];
    coverError.value = "";
    showCoverDialog.value = true;
    loadCoverCandidates();
}

function closeCoverDialog() {
    if (coverApplying.value) return;
    showCoverDialog.value = false;
    coverTargetEpisode.value = null;
    coverCandidates.value = [];
    coverError.value = "";
}

async function loadCoverCandidates() {
    if (!coverTargetEpisode.value?.id) return;
    coverLoading.value = true;
    coverError.value = "";
    try {
        const data = await podcastsAPI.generateCoverOptions(
            coverTargetEpisode.value.id,
            { count: 4 },
        );
        coverCandidates.value = data.candidates || [];
    } catch (error) {
        console.error("生成封面候选图失败:", error);
        coverError.value = error.response?.data?.error || "生成封面候选图失败";
    } finally {
        coverLoading.value = false;
    }
}

async function applyCoverCandidate(candidate) {
    if (!coverTargetEpisode.value?.id || !candidate?.path) return;
    coverApplying.value = true;
    coverError.value = "";
    try {
        await podcastsAPI.applyCoverOption(coverTargetEpisode.value.id, {
            candidate_path: candidate.path,
        });
        ElMessage.success("封面已应用");
        await loadGenerationQueue();
        closeCoverDialog();
    } catch (error) {
        console.error("应用封面失败:", error);
        coverError.value = error.response?.data?.error || "应用封面失败";
    } finally {
        coverApplying.value = false;
    }
}

function toggleQueueFilter(status) {
    if (!status) return;
    const index = queueFilters.value.indexOf(status);
    if (index >= 0) {
        queueFilters.value.splice(index, 1);
    } else {
        queueFilters.value.push(status);
    }
    if (queueFilters.value.length === 0) {
        queueFilters.value.push(status);
    }
    loadGenerationQueue();
}

// 处理热搜选择
function handleTrendingSelect({ item, source }) {
    if (!currentSession.value?.id) {
        ElMessage.warning("请先创建或选择一个会话");
        return;
    }

    // 自动填充到输入框
    const prompt = `帮我基于"${item.title}"这个热门话题创作一个音频脚本。请先搜索获取最新信息。`;
    userMessage.value = prompt;

    ElMessage.success(`已选择来自 ${source} 的话题`);

    // 可选：自动滚动到输入框
    nextTick(() => {
        const textarea = document.querySelector(".chat-input textarea");
        if (textarea) {
            textarea.focus();
        }
    });
}

// 发送消息
async function sendMessage() {
    if (!userMessage.value.trim() || aiThinking.value) return;

    if (!currentSession.value?.id) {
        ElMessage.error("会话未正确初始化，请刷新页面重试");
        return;
    }

    const message = userMessage.value.trim();
    userMessage.value = "";
    aiThinking.value = true;

    if (!currentSession.value.chat_history) {
        currentSession.value.chat_history = [];
    }

    const localMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
        pending: true,
    };

    currentSession.value.chat_history.push(localMessage);
    const typingMessage = {
        role: "assistant",
        content: "正在思考...",
        timestamp: null,
        typing: true,
    };
    currentSession.value.chat_history.push(typingMessage);
    await nextTick();
    scrollToBottom();

    try {
        // 检测是否可能需要搜索
        const searchKeywords = [
            "今天",
            "昨天",
            "最近",
            "最新",
            "沪指",
            "股市",
            "新闻",
            "热点",
            "搜索",
            "查询",
        ];
        const needsSearch = searchKeywords.some((keyword) =>
            message.includes(keyword),
        );

        if (needsSearch) {
            typingMessage.content = "正在搜索实时信息...";
            await nextTick();
        }

        const data = await podcastsAPI.chatWithAI(
            currentSession.value.id,
            message,
        );
        localMessage.pending = false;

        if (data.has_script_update) {
            currentSession.value.chat_history =
                currentSession.value.chat_history.filter(
                    (msg) => msg !== typingMessage,
                );
            await loadSession(currentSession.value.id);
        } else {
            const aiReply = data.message || "AI 已完成处理";
            typingMessage.typing = false;
            typingMessage.content = aiReply;
            typingMessage.timestamp = new Date().toISOString();
            if (
                data.script &&
                (!currentSession.value.current_script ||
                    data.script !== currentSession.value.current_script)
            ) {
                currentSession.value.current_script = data.script;
            }
            await nextTick();
            scrollToBottom();
        }
    } catch (error) {
        console.error("发送消息失败:", error);
        localMessage.pending = false;
        typingMessage.typing = false;

        let errorMsg = "发送失败，请重试";

        if (
            error.code === "ECONNABORTED" ||
            error.message?.includes("timeout")
        ) {
            errorMsg =
                "请求超时，可能是搜索耗时较长。请刷新页面重新加载试试看。";
        } else if (error.response?.status === 500) {
            errorMsg = "服务器错误，请刷新页面重新加载试试看。";
        } else if (error.response?.status === 504) {
            errorMsg =
                "网关超时，可能是搜索耗时较长。请刷新页面重新加载试试看。";
        } else {
            errorMsg =
                error.response?.data?.error ||
                error.response?.data?.detail ||
                "发送失败，请刷新页面重新加载试试看。";
        }

        typingMessage.content = errorMsg;
        typingMessage.timestamp = new Date().toISOString();
    } finally {
        aiThinking.value = false;
    }
}

// 上传文件
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
        ElMessage.error("文件大小不能超过 10MB");
        return;
    }

    uploadFile(file);
}

async function uploadFile(file) {
    uploadProgress.value = 0;

    try {
        const progressInterval = setInterval(() => {
            if (uploadProgress.value < 90) {
                uploadProgress.value += 10;
            }
        }, 200);

        await podcastsAPI.uploadReference(currentSession.value.id, file);

        clearInterval(progressInterval);
        uploadProgress.value = 100;

        setTimeout(() => {
            showUploadDialog.value = false;
            uploadProgress.value = 0;
            loadSession(currentSession.value.id);
        }, 500);
    } catch (error) {
        console.error("上传文件失败:", error);
        ElMessage.error("上传文件失败，请稍后重试");
        uploadProgress.value = 0;
    }
}

// 删除文件
async function deleteFile(fileId) {
    try {
        await ElMessageBox.confirm("确定要删除这个文件吗？", "删除文件", {
            type: "warning",
            confirmButtonText: "删除",
            cancelButtonText: "取消",
        });

        await podcastsAPI.deleteReference(currentSession.value.id, fileId);
        loadSession(currentSession.value.id);
        ElMessage.success("文件已删除");
    } catch (error) {
        if (error !== "cancel") {
            console.error("删除文件失败:", error);
            ElMessage.error("删除文件失败，请稍后重试");
        }
    }
}

// 生成音频
function openGenerateDialog() {
    if (!currentSession.value?.current_script) {
        ElMessage.warning("请先生成脚本");
        return;
    }

    showGenerateDialog.value = true;
    generateError.value = "";
    generateTitle.value = currentSession.value.title || "";
    const currentShowId = currentSession.value.show?.id ?? null;
    generateShowId.value = currentShowId;
    if (!generateHostName.value.trim()) {
        generateHostName.value = DEFAULT_HOST_NAME;
    }
    if (!generateGuestName.value.trim()) {
        generateGuestName.value = DEFAULT_GUEST_NAME;
    }
}

function closeGenerateDialog() {
    if (generating.value) return;
    showGenerateDialog.value = false;
    generateError.value = "";
}

async function confirmGeneratePodcast() {
    if (generating.value) return;

    if (!generateTitle.value.trim()) {
        generateError.value = "请输入音频标题";
        return;
    }

    generating.value = true;
    generateError.value = "";

    try {
        const payload = {
            title: generateTitle.value.trim(),
            description: "由 AI 脚本创作工具生成",
            script: currentSession.value.current_script,
        };
        applySpeakerPayload(payload, {
            hostName: generateHostName.value,
            guestName: generateGuestName.value,
            hostVoiceId: generateHostVoiceId.value,
            guestVoiceId: generateGuestVoiceId.value,
        });
        const selectedShowId = Number(
            generateShowId.value ?? currentSession.value.show?.id ?? 0,
        );
        if (Number.isInteger(selectedShowId) && selectedShowId > 0) {
            payload.show_id = selectedShowId;
        }
        await podcastsAPI.generateEpisode(payload);

        showGenerateDialog.value = false;
        ElMessage.success({
            message: "音频生成任务已提交！",
            description: '请稍后在右侧"生成记录"中查看进度',
            duration: 3000,
        });
        await loadGenerationQueue();
    } catch (error) {
        console.error("生成音频失败:", error);
        generateError.value =
            error.response?.data?.error ||
            error.response?.data?.detail ||
            "请稍后重试";
    } finally {
        generating.value = false;
    }
}

// 复制脚本
function copyScript() {
    navigator.clipboard.writeText(currentSession.value.current_script);
    ElMessage.success("脚本已复制到剪贴板");
}

// 开始编辑脚本
function startEditScript() {
    editableScript.value = currentSession.value.current_script || "";
    isEditingScript.value = true;
}

// 取消编辑脚本
function cancelScriptEdit() {
    isEditingScript.value = false;
    editableScript.value = "";
}

// 保存脚本编辑
async function saveScriptEdit() {
    if (!editableScript.value.trim()) {
        ElMessage.warning("脚本内容不能为空");
        return;
    }

    if (!currentSession.value?.id) {
        ElMessage.warning("会话未创建");
        return;
    }

    try {
        // 调用 API 保存到后端
        await podcastsAPI.updateScriptSession(currentSession.value.id, {
            current_script: editableScript.value,
        });

        // 更新本地状态
        currentSession.value.current_script = editableScript.value;
        isEditingScript.value = false;
        ElMessage.success("脚本已保存");
    } catch (error) {
        console.error("保存脚本失败:", error);
        ElMessage.error(error.response?.data?.error || "保存失败");
    }
}

async function previewSelectedSegment() {
    const segment = selectedSegment.value;
    if (!segment || !currentSession.value?.id) return;

    segmentPreviewLoading.value = true;
    try {
        const data = await podcastsAPI.previewScriptSegment(
            currentSession.value.id,
            {
                segment_text: segment.raw,
            },
        );
        segmentPreviewUrl.value = data.preview_url || "";
        ElMessage.success("试听音频已生成");
    } catch (error) {
        console.error("生成试听片段失败:", error);
        ElMessage.error(error.response?.data?.error || "试听生成失败");
    } finally {
        segmentPreviewLoading.value = false;
    }
}

async function rewriteSelectedSegment() {
    const segment = selectedSegment.value;
    const instruction = segmentRewriteInstruction.value.trim();
    if (!segment || !currentSession.value?.id || !instruction) return;

    segmentRewriteLoading.value = true;
    try {
        const data = await podcastsAPI.rewriteScriptSegment(
            currentSession.value.id,
            {
                segment_text: segment.raw,
                instruction,
            },
        );
        const rewritten = (data.rewritten_segment || "").trim();
        if (!rewritten) {
            ElMessage.error("改写结果为空");
            return;
        }

        const parts = parseScriptSegments(
            currentSession.value.current_script || "",
        );
        if (!parts.length || segment.index >= parts.length) {
            ElMessage.error("脚本片段已变化，请重试");
            return;
        }
        parts[segment.index] = {
            ...parts[segment.index],
            raw: rewritten,
        };
        currentSession.value.current_script = parts
            .map((item) => item.raw)
            .join("\n\n");
        segmentRewriteInstruction.value = "";
        ElMessage.success("局部改写成功");
    } catch (error) {
        console.error("局部改写失败:", error);
        ElMessage.error(error.response?.data?.error || "局部改写失败");
    } finally {
        segmentRewriteLoading.value = false;
    }
}

// 查看历史版本
function viewVersion(version) {
    viewingVersion.value = version;
    showVersionDialog.value = true;
}

// 恢复历史版本
async function restoreVersion(version) {
    try {
        await ElMessageBox.confirm(
            "确定要恢复到这个版本吗？当前脚本将被覆盖。",
            "恢复版本",
            {
                type: "warning",
                confirmButtonText: "恢复",
                cancelButtonText: "取消",
            },
        );

        currentSession.value.current_script = version.script;
        showVersionDialog.value = false;
        ElMessage.success("已恢复到版本 " + version.version);
    } catch (error) {
        // 用户取消
    }
}

// 工具函数
function scrollToBottom() {
    if (chatMessages.value) {
        chatMessages.value.scrollTop = chatMessages.value.scrollHeight;
    }
}

function formatDate(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("zh-CN");
}

function formatTime(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleString("zh-CN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatStatus(status) {
    const map = {
        draft: "草稿",
        processing: "生成中",
        published: "已发布",
        failed: "生成失败",
    };
    return map[status] || status;
}

function statusClass(status) {
    return (
        {
            draft: "status-badge status-draft",
            processing: "status-badge status-processing",
            published: "status-badge status-published",
            failed: "status-badge status-failed",
        }[status] || "status-badge"
    );
}

function formatStage(episode) {
    if (!episode) return "";
    if (episode.status === "failed" && !episode.generation_stage) {
        return "失败";
    }
    const stage = episode.generation_stage;
    const map = {
        queued: "排队中",
        source_fetching: "抓取中",
        script_generating: "写稿中",
        audio_generating: "TTS 生成中",
        cover_generating: "封面生成中",
        completed: "完成",
        failed: "失败",
    };
    return map[stage] || map[episode.status] || "处理中";
}

function generationProgress(episode) {
    const stage = episode?.generation_stage;
    const progressMap = {
        queued: 5,
        source_fetching: 20,
        script_generating: 45,
        audio_generating: 75,
        cover_generating: 90,
        completed: 100,
        failed: 100,
    };
    if (episode?.status === "published") return 100;
    if (episode?.status === "failed" && !stage) return 100;
    return progressMap[stage] ?? (episode?.status === "processing" ? 50 : 0);
}

function formatMessage(content) {
    if (!content) return "";

    // 1. 先移除最外层的 markdown 代码块标记（如果有）
    let text = content.trim();
    if (text.startsWith("```markdown") || text.startsWith("```")) {
        text = text.replace(/^```(?:markdown)?\n?/, "");
        text = text.replace(/\n?```$/, "");
    }

    // 2. 处理标题
    text = text.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
    text = text.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
    text = text.replace(/^# (.*?)$/gm, "<h1>$1</h1>");

    // 3. 处理粗体
    text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // 4. 处理斜体
    text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // 5. 处理【角色】标记
    text = text.replace(
        /【(.*?)】/g,
        '<strong class="role-tag">【$1】</strong>',
    );

    // 6. 最后处理换行
    text = text.replace(/\n\n/g, "<br><br>");
    text = text.replace(/\n/g, "<br>");

    return text;
}

onMounted(() => {
    loadTTSVoices();
    loadSessions();
    loadMyShows();
    loadGenerationQueue();
});
</script>

<style scoped>
.ai-script-studio {
    padding: var(--spacing-xl) 0;
}

.page-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
}

.page-title {
    font-size: var(--font-3xl);
    font-weight: var(--font-bold);
    margin: 0;
}

.page-head-btn {
    white-space: nowrap;
}

/* 会话列表 */
.session-list-view {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
}

.entry-hub {
    padding: var(--spacing-lg);
}

.entry-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
}

.entry-header h2 {
    margin: 0 0 var(--spacing-xs);
    font-size: var(--font-xl);
    font-weight: var(--font-semibold);
}

.entry-header-links {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
}

.entry-subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: var(--font-sm);
}

.mode-tabs {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--spacing-sm);
}

.mode-tab {
    border: var(--border-width) solid var(--border-color-light);
    background: var(--color-white);
    border-radius: var(--radius-default);
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: var(--font-sm);
    font-weight: var(--font-semibold);
    cursor: pointer;
    transition: var(--transition);
}

.mode-tab:hover {
    border-color: var(--color-primary);
}

.mode-tab.active {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: rgba(255, 81, 59, 0.08);
}

.mode-panel {
    margin-top: var(--spacing-md);
}

.actions {
    margin-bottom: var(--spacing-xl);
    display: flex;
    gap: var(--spacing-sm);
}

.sessions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--spacing-lg);
}

.session-card {
    cursor: pointer;
    transition: var(--transition);
}

.session-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.session-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.session-title {
    font-size: var(--font-lg);
    font-weight: var(--font-bold);
    margin: 0;
}

.session-meta {
    display: flex;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-sm);
    color: var(--color-text-tertiary);
    font-size: var(--font-sm);
}

.delete-button {
    background: none;
    border: none;
    color: var(--color-warning-dark);
    font-size: var(--font-sm);
    cursor: pointer;
    padding: 0;
    white-space: nowrap;
}

.delete-button:hover {
    color: var(--color-warning);
    text-decoration: underline;
}

.session-preview {
    color: var(--color-text-secondary);
    font-size: var(--font-sm);
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
}

.section-header h2 {
    margin: 0;
    font-size: var(--font-xl);
    font-weight: var(--font-semibold);
}

.section-link {
    color: var(--color-primary);
    font-size: var(--font-sm);
    font-weight: var(--font-semibold);
}

.generation-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.queue-filters {
    display: flex;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
}

.queue-filter {
    padding: 6px 14px;
    border-radius: 999px;
    border: var(--border-width) solid var(--border-color-light);
    background: var(--color-white);
    font-size: var(--font-xs);
    cursor: pointer;
    transition: var(--transition);
}

.queue-filter.active {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: rgba(255, 81, 59, 0.1);
}

.generation-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    border: var(--border-width) solid var(--border-color-light);
    border-radius: var(--radius-default);
    background: var(--color-white);
    cursor: pointer;
    transition: var(--transition);
}

.generation-info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
}

.generation-item:hover {
    border-color: var(--color-primary);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.generation-title {
    font-weight: var(--font-semibold);
    font-size: var(--font-base);
}

.generation-meta {
    display: flex;
    gap: var(--spacing-md);
    color: var(--color-text-tertiary);
    font-size: var(--font-xs);
}

.generation-stage-row {
    margin-top: 4px;
    display: flex;
    justify-content: space-between;
    gap: var(--spacing-sm);
    font-size: var(--font-xs);
    color: var(--color-text-secondary);
}

.generation-stage-progress {
    width: 100%;
    height: 6px;
    border-radius: 999px;
    background: var(--color-bg-secondary);
    overflow: hidden;
    margin-top: 4px;
}

.generation-stage-progress-bar {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #6dcad0, #ff513b);
    transition: width 0.3s ease;
}

.generation-error {
    margin-top: 6px;
    font-size: var(--font-xs);
    color: var(--color-primary);
    max-width: 560px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.generation-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.status-badge {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: var(--font-xs);
    font-weight: var(--font-semibold);
    text-transform: uppercase;
}

.status-processing {
    background: rgba(255, 197, 62, 0.12);
    color: var(--color-warning-dark);
}

.status-failed {
    background: rgba(255, 81, 59, 0.12);
    color: var(--color-primary);
}

.status-published {
    background: rgba(109, 202, 208, 0.15);
    color: var(--color-success-dark);
}

.status-draft {
    background: rgba(113, 128, 150, 0.12);
    color: var(--color-text-tertiary);
}

.queue-action {
    border: var(--border-width) solid var(--border-color);
    background: transparent;
    border-radius: 999px;
    padding: 4px 12px;
    font-size: var(--font-xs);
    cursor: pointer;
    transition: var(--transition);
}

.queue-action:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
}

.queue-action-cancel {
    border-color: var(--color-warning-dark);
    color: var(--color-warning-dark);
}

.queue-action-cancel:hover {
    background: rgba(255, 197, 62, 0.12);
}

.queue-action-retry {
    border-color: var(--color-success-dark);
    color: var(--color-success-dark);
}

.queue-action-retry:hover {
    background: rgba(109, 202, 208, 0.12);
}

/* 工作区 */
.workspace-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
}

.header-left {
    display: flex;
    gap: var(--spacing-lg);
    align-items: flex-start;
}

.title-block {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.workspace-title {
    font-size: var(--font-2xl);
    font-weight: var(--font-bold);
}

.workspace-meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
    font-size: var(--font-sm);
    color: var(--color-text-tertiary);
}

.meta-item {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
}

.meta-item .label {
    color: var(--color-text-secondary);
}

.workspace-actions {
    display: flex;
    gap: var(--spacing-md);
}

.delete-session-btn {
    border: 1px solid var(--color-warning-dark);
    color: var(--color-warning-dark);
    background: transparent;
}

.delete-session-btn:hover {
    background: var(--color-warning);
    color: var(--color-white);
}

.delete-session-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.workspace-content {
    display: grid;
    grid-template-columns: minmax(0, 1.8fr) minmax(300px, 1fr);
    gap: var(--spacing-lg);
    align-items: stretch;
    overflow-x: hidden;
}

/* 面板通用样式 */
.chat-panel,
.script-panel {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 280px);
    min-height: 600px;
    max-width: 100%;
    overflow-x: hidden;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
    padding-bottom: var(--spacing-xs);
    border-bottom: var(--border-width) solid var(--border-color);
}

.panel-header h3 {
    font-size: var(--font-base);
    font-weight: var(--font-semibold);
}

.header-actions {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
}

/* 参考文件 */
.reference-files {
    margin-bottom: var(--spacing-sm);
    background: var(--color-bg-secondary);
    border-radius: var(--radius-sm);
    padding: var(--spacing-sm);
}

.files-header {
    font-weight: var(--font-semibold);
    margin-bottom: var(--spacing-xs);
    font-size: 11px;
    color: var(--color-text-secondary);
}

.files-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.file-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    background: var(--color-white);
    padding: 4px var(--spacing-xs);
    border-radius: var(--radius-sm);
    font-size: 12px;
}

.file-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.file-size {
    color: var(--color-text-tertiary);
    font-size: 10px;
}

.btn-delete {
    background: none;
    border: none;
    color: var(--color-primary);
    font-size: 11px;
    cursor: pointer;
    padding: 0;
}

/* 对话消息 */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    margin-bottom: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-xs);
}

.chat-welcome {
    color: var(--color-text-tertiary);
    padding: var(--spacing-md);
    font-size: var(--font-sm);
}

.chat-welcome ul {
    margin-top: var(--spacing-xs);
    padding-left: var(--spacing-md);
}

.message {
    display: flex;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-sm);
    align-items: flex-start;
    width: 100%;
}

.message-role {
    font-size: var(--font-xs);
    font-weight: var(--font-semibold);
    color: var(--color-text-tertiary);
    min-width: 32px;
    flex-shrink: 0;
}

.message-content {
    flex: 1;
    min-width: 0;
    background: var(--color-bg);
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    word-wrap: break-word;
    overflow-wrap: break-word;
    font-size: var(--font-sm);
    line-height: 1.5;
}

.message.assistant .message-content {
    background: var(--color-bg-secondary);
    border-left: 3px solid var(--color-primary);
}

.message.typing .message-content {
    display: flex;
    align-items: center;
}

.message.system .message-content {
    background: rgba(109, 202, 208, 0.15);
    border-left: none;
    color: var(--color-text-secondary);
}

.message-text {
    line-height: 1.5;
    white-space: normal;
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 100%;
}

.message-text * {
    max-width: 100%;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.message-text h1,
.message-text h2,
.message-text h3 {
    margin: var(--spacing-xs) 0;
    font-weight: var(--font-bold);
    line-height: 1.3;
}

.message-text h1 {
    font-size: var(--font-lg);
}

.message-text h2 {
    font-size: var(--font-base);
}

.message-text h3 {
    font-size: var(--font-sm);
}

.message-text .role-tag {
    color: var(--color-primary);
    font-weight: var(--font-bold);
    font-size: inherit;
}

.message-time {
    font-size: 10px;
    color: var(--color-text-tertiary);
    margin-top: var(--spacing-xs);
}

.message-status {
    margin-top: var(--spacing-xs);
    font-size: 10px;
    color: var(--color-primary);
}

.thinking-indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--color-text-tertiary);
    font-size: var(--font-sm);
}

.thinking-indicator .dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-text-tertiary);
    animation: thinking-bounce 1.2s infinite ease-in-out;
}

.thinking-indicator .dot:nth-child(2) {
    animation-delay: 0.2s;
}

.thinking-indicator .dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes thinking-bounce {
    0%,
    80%,
    100% {
        transform: scale(0.6);
        opacity: 0.4;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}

/* 输入框 */
.chat-input {
    display: flex;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs);
    background: var(--color-bg);
    border-radius: var(--radius-default);
}

.chat-input textarea {
    flex: 1;
    padding: var(--spacing-xs);
    border: var(--border-width) solid var(--border-color);
    border-radius: var(--radius-sm);
    font-family: inherit;
    font-size: var(--font-sm);
    resize: vertical;
    min-height: 60px;
    overflow-x: hidden;
    line-height: 1.5;
}

.chat-input textarea:focus {
    outline: none;
    border-color: var(--color-primary);
}

.chat-input textarea:disabled {
    background: var(--color-bg);
    color: var(--color-text-tertiary);
}

/* 脚本预览 */
.script-meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
    font-size: 11px;
    color: var(--color-text-tertiary);
}

.script-content {
    flex: 1;
    overflow-y: auto;
    margin-bottom: var(--spacing-sm);
}

.script-empty {
    color: var(--color-text-tertiary);
    padding: var(--spacing-md);
    font-size: var(--font-sm);
}

.hint {
    color: var(--color-text-placeholder);
    font-size: 11px;
    margin-top: var(--spacing-xs);
}

.error-message {
    margin-top: var(--spacing-xs);
    color: var(--color-primary);
    font-size: var(--font-sm);
}

.script-text {
    white-space: pre-wrap;
    font-family: "Courier New", monospace;
    line-height: 1.6;
    padding: var(--spacing-sm);
    background: var(--color-bg);
    border-radius: var(--radius-sm);
    margin: 0;
    font-size: 13px;
}

.script-editor {
    width: 100%;
    height: 100%;
    min-height: 400px;
    padding: var(--spacing-md);
    font-family: "Courier New", monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-text-primary);
    background: var(--color-white);
    border: 2px solid var(--border-color);
    border-radius: var(--radius-default);
    resize: vertical;
    outline: none;
    transition: var(--transition-fast);
    box-shadow: inset 2px 2px 0 rgba(0, 0, 0, 0.05);
}

.script-editor:focus {
    border-color: var(--color-primary);
    box-shadow:
        inset 2px 2px 0 rgba(0, 0, 0, 0.05),
        0 0 0 3px rgba(255, 81, 59, 0.1);
}

.panel-actions {
    display: flex;
    gap: var(--spacing-xs);
}

.segment-tools {
    border-top: var(--border-width) solid var(--border-color);
    padding-top: var(--spacing-md);
    margin-top: var(--spacing-sm);
}

.segment-tools-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.segment-tools-header h4 {
    margin: 0;
    font-size: var(--font-base);
    font-weight: var(--font-semibold);
}

.segment-controls {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.segment-selected {
    margin-bottom: var(--spacing-sm);
}

.segment-label {
    font-size: var(--font-xs);
    color: var(--color-text-tertiary);
    margin-bottom: 4px;
}

.segment-instruction {
    width: 100%;
    min-height: 72px;
    resize: vertical;
    border: var(--border-width) solid var(--border-color);
    border-radius: var(--radius-default);
    padding: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.segment-audio {
    width: 100%;
}

.script-versions {
    border-top: var(--border-width) solid var(--border-color);
    padding-top: var(--spacing-md);
}

.versions-header {
    font-weight: var(--font-semibold);
    margin-bottom: var(--spacing-sm);
    font-size: var(--font-sm);
}

.versions-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    max-height: 150px;
    overflow-y: auto;
}

.version-item {
    background: var(--color-bg);
    border: none;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    text-align: left;
    cursor: pointer;
    font-size: var(--font-xs);
    transition: var(--transition);
}

.version-item:hover {
    background: var(--color-bg-secondary);
}

/* 模态框 */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    width: 90%;
    max-width: 500px;
}

.modal-content:hover {
    border-color: var(--border-color) !important;
    box-shadow: var(--shadow-md) !important;
    background: var(--color-white) !important;
}

.modal-content.version-modal {
    max-width: 800px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
}

.modal-content.version-modal .modal-body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.version-meta {
    display: flex;
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: var(--border-width) solid var(--border-color);
    font-size: var(--font-sm);
    color: var(--color-text-secondary);
}

.version-script-content {
    flex: 1;
    overflow-y: auto;
    background: var(--color-bg);
    border-radius: var(--radius-default);
    padding: var(--spacing-md);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: var(--border-width) solid var(--border-color);
}

.modal-header h3 {
    margin: 0;
    font-size: var(--font-lg);
}

.btn-close {
    background: none;
    border: none;
    font-size: var(--font-2xl);
    cursor: pointer;
    color: var(--color-text-tertiary);
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-body {
    margin-bottom: var(--spacing-md);
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    padding-top: var(--spacing-md);
    border-top: var(--border-width) solid var(--border-color);
}

.cover-modal {
    max-width: 860px;
}

.cover-toolbar {
    display: flex;
    justify-content: flex-end;
    margin-bottom: var(--spacing-sm);
}

.cover-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--spacing-md);
}

.cover-item {
    border: var(--border-width) solid var(--border-color-light);
    border-radius: var(--radius-default);
    padding: var(--spacing-sm);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.cover-image {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    border-radius: var(--radius-default);
    background: var(--color-bg);
}

.form-group {
    margin-bottom: var(--spacing-md);
}

.form-group label {
    display: block;
    margin-bottom: var(--spacing-xs);
    font-weight: var(--font-semibold);
    font-size: var(--font-sm);
}

.form-input,
.form-select {
    width: 100%;
    padding: var(--spacing-sm);
    border: var(--border-width) solid var(--border-color);
    border-radius: var(--radius-default);
    font-size: var(--font-base);
}

.form-input:focus,
.form-select:focus {
    outline: none;
    border-color: var(--color-primary);
}

.file-input {
    width: 100%;
    padding: var(--spacing-sm);
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-default);
    cursor: pointer;
}

.upload-progress {
    margin-top: var(--spacing-md);
    background: var(--color-bg);
    border-radius: var(--radius-default);
    height: 32px;
    position: relative;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: var(--gradient-bar);
    transition: width 0.3s;
}

.upload-progress span {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: var(--font-semibold);
    font-size: var(--font-sm);
}

.loading-state,
.empty-state {
    text-align: center;
    padding: var(--spacing-3xl);
    color: var(--color-text-tertiary);
}

.loading-state.small,
.empty-state.small {
    padding: var(--spacing-xl);
}

.rss-section {
    margin-bottom: var(--spacing-xl);
}

.debate-section {
    margin-bottom: var(--spacing-xl);
}

.rss-form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--spacing-md);
}

.speaker-config {
    grid-column: 1 / -1;
    border: var(--border-width) solid var(--border-color-light);
    border-radius: var(--radius-default);
    padding: var(--spacing-sm);
    background: var(--color-bg);
}

.speaker-config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.speaker-config-header > label {
    margin: 0;
    font-size: var(--font-sm);
    font-weight: var(--font-semibold);
}

.speaker-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--spacing-sm);
}

.section-tip {
    margin: 0 0 var(--spacing-md);
    color: var(--color-text-secondary);
}

.debate-topic {
    grid-column: 1 / -1;
}

.rss-checkbox {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--font-sm);
    color: var(--color-text-secondary);
}

.rss-actions {
    display: flex;
    gap: var(--spacing-sm);
}

.rss-preview {
    margin-top: var(--spacing-md);
    max-height: 280px;
    overflow: auto;
}

.rss-script-editor {
    margin-top: var(--spacing-md);
}

.form-group-label {
    display: block;
    margin-bottom: var(--spacing-xs);
    font-weight: var(--font-semibold);
    font-size: var(--font-sm);
}

.rss-script-textarea {
    font-family: "Courier New", monospace;
    line-height: 1.6;
    min-height: 260px;
}

.code-block {
    background: var(--color-bg-secondary);
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    margin: var(--spacing-xs) 0;
    font-family: "Courier New", monospace;
    font-size: var(--font-sm);
    max-width: 100%;
}

@media (max-width: 1360px) {
    .workspace-content {
        grid-template-columns: 1fr;
    }

    .chat-panel,
    .script-panel {
        height: auto;
        min-height: auto;
    }
}

@media (max-width: 1024px) {
    .page-head {
        flex-direction: column;
        align-items: flex-start;
    }

    .entry-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .entry-header-links {
        flex-wrap: wrap;
    }

    .mode-tabs {
        grid-template-columns: 1fr;
    }

    .workspace-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--spacing-lg);
    }

    .header-left {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--spacing-md);
    }

    .workspace-actions {
        width: 100%;
        justify-content: flex-start;
    }

    .rss-form {
        grid-template-columns: 1fr;
    }

    .speaker-grid {
        grid-template-columns: 1fr;
    }

    .segment-controls {
        grid-template-columns: 1fr;
    }

    .cover-grid {
        grid-template-columns: 1fr;
    }
}
</style>
