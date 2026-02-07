<template>
    <div class="upload-episode-page">
        <div class="container">
            <h1 class="page-title">创建播客单集</h1>

            <div class="form-card mofa-card">
                <div class="ai-hint">
                    <div>
                        <h2>AI 来帮忙？</h2>
                        <p>在创作页可用链接、RSS、脚本或辩论模式直接生成音频任务。</p>
                    </div>
                    <el-button type="primary" plain @click="goToAIStudio">
                        前往创作页
                    </el-button>
                </div>

                <el-divider />

                <el-form
                    :model="form"
                    :rules="uploadRules"
                    ref="uploadFormRef"
                    label-width="100px"
                >
                    <el-form-item label="单集标题" prop="title">
                        <el-input
                            v-model="form.title"
                            placeholder="输入单集标题"
                        />
                    </el-form-item>

                    <el-form-item label="单集描述" prop="description">
                        <el-input
                            v-model="form.description"
                            type="textarea"
                            :rows="5"
                            placeholder="介绍一下这一集的内容..."
                        />
                    </el-form-item>

                    <el-form-item label="音频文件" prop="audio_file">
                        <el-upload
                            class="audio-uploader"
                            :on-change="handleAudioChange"
                            :auto-upload="false"
                            accept="audio/*"
                            :show-file-list="false"
                        >
                            <el-button v-if="!audioFile" type="primary">
                                <el-icon><Upload /></el-icon>
                                选择音频文件
                            </el-button>
                            <div v-else class="audio-info">
                                <el-icon class="audio-icon"
                                    ><Headset
                                /></el-icon>
                                <span>{{ audioFile.name }}</span>
                                <el-button
                                    type="danger"
                                    text
                                    @click.stop="removeAudio"
                                >
                                    删除
                                </el-button>
                            </div>
                        </el-upload>
                        <p class="form-hint">
                            支持 MP3、WAV、M4A 等格式，最大 500MB
                        </p>
                    </el-form-item>

                    <!-- 播客专用字段 -->
                    <template v-if="showContentType === 'podcast'">
                        <el-form-item label="季数" v-show="false">
                            <el-input-number
                                v-model="form.season_number"
                                :min="1"
                            />
                        </el-form-item>

                        <el-form-item label="集数" v-show="false">
                            <el-input-number
                                v-model="form.episode_number"
                                :min="1"
                            />
                        </el-form-item>
                    </template>

                    <!-- 音乐专用字段 -->
                    <template v-if="showContentType === 'music'">
                        <el-form-item label="艺术家" prop="artist">
                            <el-input
                                v-model="form.artist"
                                placeholder="输入艺术家名称"
                            />
                        </el-form-item>

                        <el-form-item label="流派">
                            <el-input
                                v-model="form.genre"
                                placeholder="如：流行、摇滚、古典等"
                            />
                        </el-form-item>

                        <el-form-item label="专辑名">
                            <el-input
                                v-model="form.album_name"
                                placeholder="输入专辑名称（可选）"
                            />
                        </el-form-item>

                        <el-form-item label="发行日期">
                            <el-date-picker
                                v-model="form.release_date"
                                type="date"
                                placeholder="选择发行日期"
                                format="YYYY-MM-DD"
                                value-format="YYYY-MM-DD"
                            />
                        </el-form-item>
                    </template>

                    <el-divider />

                    <el-form-item label="">
                        <VisibilitySelector
                            v-model="form.visibility"
                            label="单集可见性"
                            :include-inherit="true"
                        />
                    </el-form-item>

                    <el-form-item>
                        <el-button
                            type="primary"
                            @click="handleUploadSubmit"
                            :loading="uploading"
                            :disabled="
                                uploadProgress > 0 && uploadProgress < 100
                            "
                        >
                            {{
                                uploading
                                    ? `上传中 ${uploadProgress}%`
                                    : "上传单集"
                            }}
                        </el-button>
                        <el-button @click="$router.back()">取消</el-button>
                    </el-form-item>

                    <el-progress
                        v-if="uploadProgress > 0"
                        :percentage="uploadProgress"
                    />
                </el-form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/api";
import { ElMessage } from "element-plus";
import { Upload, Headset } from "@element-plus/icons-vue";
import VisibilitySelector from "@/components/common/VisibilitySelector.vue";

const route = useRoute();
const router = useRouter();

// 节目信息
const showContentType = ref("podcast");

// 上传模式
const uploadFormRef = ref();
const uploading = ref(false);
const uploadProgress = ref(0);
const audioFile = ref(null);

const form = ref({
    show_id: null,
    title: "",
    description: "",
    audio_file: null,
    season_number: 1,
    episode_number: 1,
    // 音乐字段
    artist: "",
    genre: "",
    album_name: "",
    release_date: null,
    // 可见性
    visibility: "inherit",
});

const uploadRules = {
    title: [{ required: true, message: "请输入单集标题", trigger: "blur" }],
    description: [
        { required: true, message: "请输入单集描述", trigger: "blur" },
    ],
    audio_file: [
        { required: true, message: "请上传音频文件", trigger: "change" },
    ],
};

onMounted(async () => {
    const showSlug = route.params.slug;

    try {
        const show = await api.podcasts.getShow(showSlug);
        form.value.show_id = show.id;
        showContentType.value = show.content_type || "podcast";
    } catch (error) {
        console.error("Failed to fetch show info:", error);
        ElMessage.error("加载节目失败，请稍后重试");
        router.back();
    }
});

function goToAIStudio() {
    router.push("/creator/ai-studio");
}

function handleAudioChange(file) {
    audioFile.value = file;
    form.value.audio_file = file.raw;
}

function removeAudio() {
    audioFile.value = null;
    form.value.audio_file = null;
}

async function handleUploadSubmit() {
    const valid = await uploadFormRef.value.validate().catch(() => false);
    if (!valid) return;
    if (!form.value.show_id) {
        ElMessage.error("节目信息加载失败，请刷新后重试");
        return;
    }

    uploading.value = true;
    uploadProgress.value = 0;

    try {
        const formData = new FormData();
        formData.append("show_id", form.value.show_id);
        formData.append("title", form.value.title);
        formData.append("description", form.value.description);
        formData.append("audio_file", form.value.audio_file);
        formData.append("visibility", form.value.visibility);

        // 播客字段
        if (showContentType.value === "podcast") {
            formData.append("season_number", form.value.season_number);
            formData.append("episode_number", form.value.episode_number);
        }

        // 音乐字段
        if (showContentType.value === "music") {
            if (form.value.artist) formData.append("artist", form.value.artist);
            if (form.value.genre) formData.append("genre", form.value.genre);
            if (form.value.album_name)
                formData.append("album_name", form.value.album_name);
            if (form.value.release_date)
                formData.append("release_date", form.value.release_date);
        }

        await api.podcasts.createEpisode(formData);

        ElMessage.success("上传成功！音频正在处理中...");
        router.push("/creator");
    } catch (error) {
        // 错误已处理
    } finally {
        uploading.value = false;
        uploadProgress.value = 0;
    }
}
</script>

<style scoped>
.upload-episode-page {
    padding: var(--spacing-xl) 0;
}

.page-title {
    font-size: var(--font-3xl);
    font-weight: var(--font-bold);
    margin-bottom: var(--spacing-xl);
}

.form-card {
    max-width: 800px;
    padding: var(--spacing-xl);
}

.ai-hint {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-lg);
    background: var(--color-bg-secondary);
    padding: var(--spacing-lg);
    border-radius: var(--radius-default);
}

.ai-hint h2 {
    margin: 0 0 var(--spacing-xs) 0;
    font-size: var(--font-lg);
    font-weight: var(--font-semibold);
}

.ai-hint p {
    margin: 0;
    color: var(--color-text-secondary);
}

.audio-uploader {
    width: 100%;
}

.audio-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: var(--color-bg-secondary);
    border-radius: var(--radius-default);
    border: 2px solid var(--border-color-light);
}

.audio-icon {
    font-size: 24px;
    color: var(--color-primary);
}

.form-hint {
    font-size: var(--font-sm);
    color: var(--color-text-tertiary);
    margin-top: var(--spacing-xs);
}

@media (max-width: 768px) {
    .upload-episode-page {
        padding: var(--spacing-lg) 0;
    }

    .page-title {
        font-size: var(--font-2xl);
        margin-bottom: var(--spacing-lg);
    }

    .form-card {
        padding: var(--spacing-lg);
    }

    .ai-hint {
        flex-direction: column;
        align-items: flex-start;
    }
}

@media (max-width: 480px) {
    .upload-episode-page {
        padding: var(--spacing-md) 0;
    }

    .page-title {
        font-size: var(--font-xl);
    }

    .form-card {
        padding: var(--spacing-md);
    }

    .audio-info {
        flex-wrap: wrap;
    }
}
</style>
