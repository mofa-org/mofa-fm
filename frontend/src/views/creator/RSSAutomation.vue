<template>
  <div class="rss-automation-page">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">RSS 自动化</h1>
          <p class="page-subtitle">维护 RSS 源、列表与每日定时生成规则。</p>
        </div>
        <button class="mofa-btn" @click="loadAll">刷新</button>
      </div>

      <section class="mofa-card section-card">
        <h2 class="section-title">我的源</h2>
        <div class="form-grid">
          <input v-model="sourceForm.name" class="form-input" placeholder="源名称，如 HN" />
          <input v-model="sourceForm.url" class="form-input" placeholder="https://news.ycombinator.com/rss" />
          <input v-model="sourceForm.description" class="form-input" placeholder="备注（可选）" />
          <button class="mofa-btn mofa-btn-primary" :disabled="submittingSource" @click="createSource">
            {{ submittingSource ? "提交中..." : "添加源" }}
          </button>
        </div>
        <div class="list-table" v-if="sources.length">
          <div class="list-row" v-for="item in sources" :key="item.id">
            <div class="list-main">
              <div class="list-title">{{ item.name }}</div>
              <div class="list-meta">{{ item.url }}</div>
            </div>
            <div class="list-actions">
              <button class="mofa-btn mofa-btn-sm" @click="toggleSource(item)">
                {{ item.is_active ? "停用" : "启用" }}
              </button>
              <button class="mofa-btn mofa-btn-sm mofa-btn-danger" @click="removeSource(item)">删除</button>
            </div>
          </div>
        </div>
        <p v-else class="empty-tip">暂无 RSS 源。</p>
      </section>

      <section class="mofa-card section-card">
        <h2 class="section-title">源列表</h2>
        <div class="form-grid">
          <input v-model="listForm.name" class="form-input" placeholder="列表名，如 科技晨报" />
          <input v-model="listForm.description" class="form-input" placeholder="描述（可选）" />
          <select v-model="listForm.source_ids" class="form-input" multiple>
            <option v-for="item in activeSources" :key="item.id" :value="item.id">
              {{ item.name }}
            </option>
          </select>
          <button class="mofa-btn mofa-btn-primary" :disabled="submittingList" @click="createList">
            {{ submittingList ? "提交中..." : "创建列表" }}
          </button>
        </div>
        <div class="list-table" v-if="rssLists.length">
          <div class="list-row" v-for="item in rssLists" :key="item.id">
            <div class="list-main">
              <div class="list-title">{{ item.name }}</div>
              <div class="list-meta">源数：{{ item.source_count || item.sources?.length || 0 }}</div>
            </div>
            <div class="list-actions">
              <button class="mofa-btn mofa-btn-sm" @click="toggleList(item)">
                {{ item.is_active ? "停用" : "启用" }}
              </button>
              <button class="mofa-btn mofa-btn-sm mofa-btn-danger" @click="removeList(item)">删除</button>
            </div>
          </div>
        </div>
        <p v-else class="empty-tip">暂无源列表。</p>
      </section>

      <section class="mofa-card section-card">
        <h2 class="section-title">自动规则</h2>
        <div class="schedule-grid">
          <input v-model="scheduleForm.name" class="form-input" placeholder="规则名，如 每日科技快报" />
          <select v-model="scheduleForm.rss_list_id" class="form-input">
            <option :value="null">选择 RSS 列表</option>
            <option v-for="item in activeLists" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <select v-model="scheduleForm.show_id" class="form-input">
            <option :value="null">默认频道（自动）</option>
            <option v-for="show in myShows" :key="show.id" :value="show.id">{{ show.title }}</option>
          </select>
          <input v-model="scheduleForm.run_time" type="time" class="form-input" />
          <select v-model="scheduleForm.frequency" class="form-input">
            <option value="daily">每天</option>
            <option value="weekly">每周</option>
          </select>
          <input v-model="scheduleForm.timezone_name" class="form-input" placeholder="时区，如 Asia/Shanghai" />
          <select v-model="scheduleForm.template" class="form-input">
            <option value="news_flash">新闻快报</option>
            <option value="web_summary">网页摘要</option>
            <option value="deep_dive">深度长谈</option>
          </select>
          <input v-model.number="scheduleForm.max_items" type="number" min="1" max="20" class="form-input" placeholder="条目数" />
          <select v-model="scheduleForm.sort_by" class="form-input">
            <option value="latest">最新优先</option>
            <option value="oldest">最早优先</option>
            <option value="title">按标题</option>
          </select>
          <label class="checkbox-line">
            <input v-model="scheduleForm.deduplicate" type="checkbox" />
            去重（标题+链接）
          </label>
          <input v-model="scheduleForm.host_name" class="form-input" placeholder="主持人名（默认大牛）" />
          <input v-model="scheduleForm.guest_name" class="form-input" placeholder="嘉宾名（默认一帆）" />
        </div>
        <div v-if="scheduleForm.frequency === 'weekly'" class="week-days">
          <label v-for="item in weekDayOptions" :key="item.value" class="checkbox-line">
            <input
              type="checkbox"
              :checked="scheduleForm.week_days.includes(item.value)"
              @change="toggleWeekDay(item.value)"
            />
            {{ item.label }}
          </label>
        </div>
        <div class="submit-row">
          <button class="mofa-btn mofa-btn-success" :disabled="submittingSchedule" @click="createSchedule">
            {{ submittingSchedule ? "提交中..." : "创建自动规则" }}
          </button>
        </div>

        <div class="list-table" v-if="schedules.length">
          <div class="list-row" v-for="item in schedules" :key="item.id">
            <div class="list-main">
              <div class="list-title">{{ item.name }}</div>
              <div class="list-meta">
                {{ item.rss_list?.name }} · {{ item.frequency === "daily" ? "每天" : "每周" }} {{ item.run_time }}
                · 下次：{{ formatTime(item.next_run_at) }}
              </div>
              <div class="list-meta" v-if="item.last_status || item.last_run_at">
                最近：{{ item.last_status || "idle" }} · {{ formatTime(item.last_run_at) }}
              </div>
              <div class="list-error" v-if="item.last_error">{{ item.last_error }}</div>
            </div>
            <div class="list-actions">
              <button class="mofa-btn mofa-btn-sm mofa-btn-primary" @click="triggerSchedule(item)">立即执行</button>
              <button class="mofa-btn mofa-btn-sm" @click="toggleSchedule(item)">
                {{ item.is_active ? "停用" : "启用" }}
              </button>
              <button class="mofa-btn mofa-btn-sm" @click="loadRuns(item.id)">查看记录</button>
              <button class="mofa-btn mofa-btn-sm mofa-btn-danger" @click="removeSchedule(item)">删除</button>
            </div>
          </div>
        </div>
        <p v-else class="empty-tip">暂无自动规则。</p>
      </section>

      <section class="mofa-card section-card">
        <h2 class="section-title">运行记录</h2>
        <div class="list-table" v-if="runs.length">
          <div class="list-row" v-for="item in runs" :key="item.id">
            <div class="list-main">
              <div class="list-title">{{ item.schedule_name }} · {{ item.status }}</div>
              <div class="list-meta">
                {{ item.trigger_type }} · {{ formatTime(item.started_at) }} · 条目 {{ item.item_count }}
              </div>
              <div class="list-error" v-if="item.error">{{ item.error }}</div>
            </div>
            <div class="list-actions" v-if="item.episode">
              <router-link :to="`/status`" class="mofa-btn mofa-btn-sm">查看单集</router-link>
            </div>
          </div>
        </div>
        <p v-else class="empty-tip">暂无运行记录。</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import podcastsAPI from "@/api/podcasts";

const sources = ref([]);
const rssLists = ref([]);
const schedules = ref([]);
const runs = ref([]);
const myShows = ref([]);

const submittingSource = ref(false);
const submittingList = ref(false);
const submittingSchedule = ref(false);

const sourceForm = ref({
  name: "",
  url: "",
  description: "",
});

const listForm = ref({
  name: "",
  description: "",
  source_ids: [],
});

const scheduleForm = ref({
  name: "",
  rss_list_id: null,
  show_id: null,
  template: "news_flash",
  max_items: 8,
  deduplicate: true,
  sort_by: "latest",
  timezone_name: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
  run_time: "08:00",
  frequency: "daily",
  week_days: [],
  host_name: "大牛",
  guest_name: "一帆",
});

const weekDayOptions = [
  { value: 0, label: "周一" },
  { value: 1, label: "周二" },
  { value: 2, label: "周三" },
  { value: 3, label: "周四" },
  { value: 4, label: "周五" },
  { value: 5, label: "周六" },
  { value: 6, label: "周日" },
];

const activeSources = computed(() => sources.value.filter((item) => item.is_active));
const activeLists = computed(() => rssLists.value.filter((item) => item.is_active));

function formatTime(value) {
  if (!value) return "-";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toggleWeekDay(value) {
  const index = scheduleForm.value.week_days.indexOf(value);
  if (index >= 0) {
    scheduleForm.value.week_days.splice(index, 1);
  } else {
    scheduleForm.value.week_days.push(value);
    scheduleForm.value.week_days.sort((a, b) => a - b);
  }
}

async function loadSources() {
  const data = await podcastsAPI.getRSSSources();
  sources.value = Array.isArray(data) ? data : data.results || [];
}

async function loadLists() {
  const data = await podcastsAPI.getRSSLists();
  rssLists.value = Array.isArray(data) ? data : data.results || [];
}

async function loadSchedules() {
  const data = await podcastsAPI.getRSSSchedules();
  schedules.value = Array.isArray(data) ? data : data.results || [];
}

async function loadRuns(scheduleId = null) {
  if (scheduleId) {
    const data = await podcastsAPI.getRSSScheduleRuns(scheduleId);
    runs.value = data.results || [];
    return;
  }
  const data = await podcastsAPI.getRSSRuns();
  runs.value = Array.isArray(data) ? data : data.results || [];
}

async function loadShows() {
  const data = await podcastsAPI.getMyShows();
  myShows.value = Array.isArray(data) ? data : data.results || [];
}

async function loadAll() {
  await Promise.all([loadSources(), loadLists(), loadSchedules(), loadRuns(), loadShows()]);
}

async function createSource() {
  if (!sourceForm.value.name.trim() || !sourceForm.value.url.trim()) {
    ElMessage.warning("请填写源名称与地址");
    return;
  }
  submittingSource.value = true;
  try {
    await podcastsAPI.createRSSSource({
      name: sourceForm.value.name.trim(),
      url: sourceForm.value.url.trim(),
      description: sourceForm.value.description.trim(),
      is_active: true,
    });
    sourceForm.value = { name: "", url: "", description: "" };
    await loadSources();
    ElMessage.success("RSS 源已添加");
  } finally {
    submittingSource.value = false;
  }
}

async function toggleSource(item) {
  await podcastsAPI.updateRSSSource(item.id, { is_active: !item.is_active });
  await loadSources();
}

async function removeSource(item) {
  await ElMessageBox.confirm(`删除源「${item.name}」？`, "确认删除", {
    type: "warning",
    confirmButtonText: "删除",
    cancelButtonText: "取消",
  });
  await podcastsAPI.deleteRSSSource(item.id);
  await loadSources();
  await loadLists();
}

async function createList() {
  if (!listForm.value.name.trim()) {
    ElMessage.warning("请填写列表名");
    return;
  }
  submittingList.value = true;
  try {
    await podcastsAPI.createRSSList({
      name: listForm.value.name.trim(),
      description: listForm.value.description.trim(),
      source_ids: listForm.value.source_ids,
      is_active: true,
    });
    listForm.value = { name: "", description: "", source_ids: [] };
    await loadLists();
    ElMessage.success("RSS 列表已创建");
  } finally {
    submittingList.value = false;
  }
}

async function toggleList(item) {
  await podcastsAPI.updateRSSList(item.id, { is_active: !item.is_active });
  await loadLists();
}

async function removeList(item) {
  await ElMessageBox.confirm(`删除列表「${item.name}」？`, "确认删除", {
    type: "warning",
    confirmButtonText: "删除",
    cancelButtonText: "取消",
  });
  await podcastsAPI.deleteRSSList(item.id);
  await loadLists();
  await loadSchedules();
}

async function createSchedule() {
  if (!scheduleForm.value.name.trim() || !scheduleForm.value.rss_list_id) {
    ElMessage.warning("请填写规则名并选择 RSS 列表");
    return;
  }
  if (scheduleForm.value.frequency === "weekly" && !scheduleForm.value.week_days.length) {
    ElMessage.warning("每周模式请至少选择一天");
    return;
  }
  submittingSchedule.value = true;
  try {
    await podcastsAPI.createRSSSchedule({
      ...scheduleForm.value,
      name: scheduleForm.value.name.trim(),
      show_id: scheduleForm.value.show_id || null,
      host_name: (scheduleForm.value.host_name || "").trim(),
      guest_name: (scheduleForm.value.guest_name || "").trim(),
      is_active: true,
    });
    await loadSchedules();
    await loadRuns();
    ElMessage.success("自动规则已创建");
  } finally {
    submittingSchedule.value = false;
  }
}

async function triggerSchedule(item) {
  await podcastsAPI.triggerRSSSchedule(item.id);
  ElMessage.success("已提交执行任务");
  await loadSchedules();
}

async function toggleSchedule(item) {
  await podcastsAPI.updateRSSSchedule(item.id, { is_active: !item.is_active });
  await loadSchedules();
}

async function removeSchedule(item) {
  await ElMessageBox.confirm(`删除规则「${item.name}」？`, "确认删除", {
    type: "warning",
    confirmButtonText: "删除",
    cancelButtonText: "取消",
  });
  await podcastsAPI.deleteRSSSchedule(item.id);
  await loadSchedules();
  await loadRuns();
}

onMounted(() => {
  loadAll();
});
</script>

<style scoped>
.rss-automation-page {
  padding: var(--spacing-xl) 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);
}

.page-title {
  margin: 0;
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-secondary);
}

.section-card {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.section-title {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.form-input {
  width: 100%;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-default);
  padding: var(--spacing-sm);
  font-size: var(--font-sm);
}

.week-days {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.checkbox-line {
  display: inline-flex;
  gap: var(--spacing-xs);
  align-items: center;
  font-size: var(--font-sm);
}

.submit-row {
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.list-table {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.list-row {
  border: var(--border-width) solid var(--border-color-light);
  border-radius: var(--radius-default);
  padding: var(--spacing-sm);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-sm);
}

.list-main {
  min-width: 0;
}

.list-title {
  font-weight: var(--font-semibold);
}

.list-meta {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  word-break: break-all;
}

.list-error {
  margin-top: var(--spacing-xs);
  font-size: var(--font-sm);
  color: var(--color-warning);
}

.list-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  justify-content: flex-end;
}

.empty-tip {
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}

@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }

  .schedule-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .form-grid,
  .schedule-grid {
    grid-template-columns: 1fr;
  }

  .list-row {
    flex-direction: column;
  }

  .list-actions {
    justify-content: flex-start;
    width: 100%;
  }
}
</style>
