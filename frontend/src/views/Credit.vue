<template>
  <div class="page-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <el-statistic title="当前余额" :value="userStore.creditBalance">
            <template #suffix>Credit</template>
          </el-statistic>
          <el-button type="primary" style="width: 100%; margin-top: 20px" @click="showChargeDialog = true">
            充值
          </el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <el-statistic title="累计充值" :value="totalPurchased">
            <template #suffix>Credit</template>
          </el-statistic>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <el-statistic title="累计消费" :value="totalSpent">
            <template #suffix>Credit</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>
        <span class="card-title">消费记录</span>
      </template>

      <el-table :data="transactions" v-loading="loading">
        <el-table-column prop="type" label="类型" width="150">
          <template #default="{ row }">
            <el-tag :type="row.amount > 0 ? 'success' : 'info'">
              {{ typeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.amount > 0 ? '#67c23a' : '#909399' }">
              {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="余额" width="120" />
        <el-table-column prop="description" label="说明" min-width="200" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 充值对话框 -->
    <el-dialog v-model="showChargeDialog" title="充值 Credit" width="500px">
      <div class="charge-packages">
        <div
          v-for="pkg in packages"
          :key="pkg.amount"
          :class="['package-card', selectedPackage === pkg.amount ? 'selected' : '']"
          @click="selectedPackage = pkg.amount"
        >
          <div class="package-amount">{{ pkg.amount }} Credit</div>
          <div class="package-price">¥{{ pkg.price }}</div>
          <div v-if="pkg.bonus" class="package-bonus">赠送 {{ pkg.bonus }} Credit</div>
        </div>
      </div>

      <el-alert
        title="提示：当前为演示环境，充值功能暂未开放"
        type="info"
        :closable="false"
        style="margin-top: 20px"
      />

      <template #footer>
        <el-button @click="showChargeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCharge" disabled>
          支付 ¥{{ getPackagePrice() }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const loading = ref(false)
const showChargeDialog = ref(false)
const selectedPackage = ref(1000)

const transactions = ref([
  {
    id: '1',
    type: 'purchase',
    amount: 1000,
    balance_after: 1000,
    description: '新用户赠送',
    created_at: new Date().toISOString()
  }
])

const packages = [
  { amount: 100, price: 10, bonus: 0 },
  { amount: 500, price: 45, bonus: 50 },
  { amount: 1000, price: 80, bonus: 150 },
  { amount: 5000, price: 350, bonus: 1000 }
]

const totalPurchased = computed(() => {
  return transactions.value
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0)
})

const totalSpent = computed(() => {
  return Math.abs(
    transactions.value
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + t.amount, 0)
  )
})

const typeText = (type) => {
  const map = {
    purchase: '充值',
    script_generation: '脚本生成',
    audio_generation: '音频生成',
    refund: '退款'
  }
  return map[type] || type
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getPackagePrice = () => {
  const pkg = packages.find(p => p.amount === selectedPackage.value)
  return pkg?.price || 0
}

const handleCharge = () => {
  ElMessage.info('演示环境暂未开放充值功能')
}

onMounted(() => {
  // 这里可以从后端加载真实的交易记录
})
</script>

<style scoped>
.card-title {
  padding: 0;
}

.charge-packages {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.package-card {
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.package-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.package-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.package-amount {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.package-price {
  font-size: 18px;
  color: #409eff;
  margin-bottom: 8px;
}

.package-bonus {
  font-size: 12px;
  color: #67c23a;
}
</style>
