<template>
  <div class="page-wrap">
    <div class="section-head">
      <div>
        <h2 class="section-title">我的环保账本 🌍</h2>
        <p class="section-sub">你每一次领取，都在让这个世界少一点浪费</p>
      </div>
    </div>

    <!-- 个人贡献 -->
    <div class="impact-banner fade-up">
      <div class="impact-left">
        <div class="impact-label">我的累计贡献</div>
        <div class="impact-main">
          <div class="impact-number">{{ mine.total_reduce_carbon || 0 }}<small> kg</small></div>
          <div class="impact-caption">减少碳排放 ≈ 种下 {{ trees }} 棵树🌳</div>
        </div>
      </div>
      <div class="impact-right">
        <div class="impact-mini"><strong>{{ mine.total_save_food || 0 }} kg</strong><span>拯救食物</span></div>
        <div class="impact-mini"><strong>{{ mine.total_order_count || 0 }} 份</strong><span>领取魔法袋</span></div>
      </div>
    </div>

    <!-- 平台数据 -->
    <div class="stat-row">
      <div class="stat-card soft-card">
        <div class="stat-icon">🥗</div>
        <div class="stat-label">平台累计拯救食物</div>
        <div class="stat-value">{{ platform.total_save_food || 0 }} <small>kg</small></div>
      </div>
      <div class="stat-card soft-card">
        <div class="stat-icon">🌿</div>
        <div class="stat-label">平台累计减碳</div>
        <div class="stat-value green">{{ platform.total_reduce_carbon || 0 }} <small>kg</small></div>
      </div>
      <div class="stat-card soft-card">
        <div class="stat-icon">🛍️</div>
        <div class="stat-label">累计完成订单</div>
        <div class="stat-value">{{ platform.total_order_count || 0 }} <small>单</small></div>
      </div>
    </div>

    <!-- 记录列表 -->
    <div class="records-card soft-card">
      <div class="records-head">减碳明细</div>
      <el-table v-loading="loading" :data="records" stripe>
        <el-table-column prop="order_id" label="订单" width="100">
          <template #default="{ row }">#{{ row.order_id }}</template>
        </el-table-column>
        <el-table-column prop="save_food_weight" label="拯救食物 (kg)" min-width="150" />
        <el-table-column prop="reduce_carbon" label="减少碳排 (kg)" min-width="150">
          <template #default="{ row }"><span class="carbon-cell">{{ row.reduce_carbon }}</span></template>
        </el-table-column>
        <el-table-column prop="create_time" label="记录时间" min-width="180">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default><el-tag type="success" effect="light" round size="small">已计入</el-tag></template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && records.length === 0" description="完成第一单后，这里就会记录你的环保贡献啦">
        <el-button type="primary" @click="$router.push('/bags')">去领第一袋</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUserStore } from '../stores/user'
import { getCarbonRecords, getCarbonSummary, getPlatformCarbon } from '../api/magic'

const userStore = useUserStore()
const loading = ref(false)
const platform = ref({})
const mine = ref({})
const records = ref([])

const trees = computed(() => Math.max(1, Math.round(Number(mine.value.total_reduce_carbon || 0) / 1.2)))

function formatTime(value) {
  return value ? String(value).slice(0, 16).replace('T', ' ') : ''
}

onMounted(async () => {
  try {
    platform.value = await getPlatformCarbon()
    const uid = userStore.info?.id
    if (uid) {
      loading.value = true
      const [summary, list] = await Promise.all([
        getCarbonSummary(uid),
        getCarbonRecords(uid),
      ])
      mine.value = summary
      records.value = list
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.section-head { margin-bottom: 20px; }
.impact-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 32px 40px;
  border-radius: 20px;
  color: #fff;
  background: linear-gradient(120deg, #2f9e60, #57bd7d 60%, #7fd39c);
  box-shadow: 0 12px 32px rgba(47, 158, 96, 0.25);
  margin-bottom: 20px;
}
.impact-label { font-size: 13px; opacity: 0.9; margin-bottom: 8px; }
.impact-number { font-size: 48px; font-weight: 800; line-height: 1; }
.impact-number small { font-size: 18px; font-weight: 500; }
.impact-caption { margin-top: 10px; font-size: 13px; opacity: 0.95; }
.impact-right { display: flex; gap: 40px; }
.impact-mini { display: flex; flex-direction: column; text-align: center; }
.impact-mini strong { font-size: 26px; }
.impact-mini span { font-size: 12px; opacity: 0.9; margin-top: 4px; }
.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { padding: 22px 24px; }
.stat-icon { font-size: 30px; margin-bottom: 8px; }
.stat-label { font-size: 13px; color: var(--ink-mute); }
.stat-value { font-size: 30px; font-weight: 800; color: var(--orange-500); margin-top: 6px; }
.stat-value.green { color: var(--green-600); }
.stat-value small { font-size: 14px; font-weight: 500; color: var(--ink-mute); }
.records-card { padding: 8px 4px 4px; }
.records-head { font-size: 16px; font-weight: 700; padding: 14px 20px; }
.carbon-cell { color: var(--green-600); font-weight: 700; }
@media (max-width: 900px) {
  .stat-row { grid-template-columns: 1fr; }
  .impact-banner { flex-direction: column; align-items: flex-start; gap: 24px; padding: 28px; }
}
</style>
