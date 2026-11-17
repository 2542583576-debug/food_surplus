<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>订单管理</span>
          <div class="stat-tabs">
            <el-radio-group v-model="filter.status" @change="load">
              <el-radio-button :value="null">全部</el-radio-button>
              <el-radio-button :value="1">待自提</el-radio-button>
              <el-radio-button :value="2">已完成</el-radio-button>
              <el-radio-button :value="3">已取消</el-radio-button>
              <el-radio-button :value="4">超时未取</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <div class="filters">
        <el-date-picker v-model="filter.pickup_date" type="date" placeholder="自提日期" value-format="YYYY-MM-DD" clearable style="width: 160px" @change="load" />
        <el-input v-model="filter.keyword" placeholder="手机号 / 订单号 / 顾客姓名" clearable style="width: 240px" @keyup.enter="load" />
        <el-button type="primary" :icon="Search" @click="load">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column label="顾客" width="140">
          <template #default="{ row }">
            <div>{{ row.customer_name || '—' }}</div>
            <div style="color: #909399; font-size: 12px">{{ row.customer_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="份数 / 金额" width="120">
          <template #default="{ row }">
            <span>{{ row.quantity }} 份</span>
            <span style="color: #f56c6c; margin-left: 4px">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="自提日期" width="110">
          <template #default="{ row }">{{ formatDate(row.pickup_date) }}</template>
        </el-table-column>
        <el-table-column label="核销码" width="110">
          <template #default="{ row }">
            <span class="verify-code">{{ row.verify_code }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status]" size="small">{{ statusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 1" type="success" size="small" @click="openVerify(row)">核销</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page" v-model:page-size="size" :total="total"
        :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        class="pagination" @change="load"
      />
    </el-card>

    <!-- 核销弹窗 -->
    <el-dialog v-model="verifyVisible" title="到店核销" width="420px">
      <div class="verify-order-info" v-if="verifyTarget">
        <p>订单号：<b>{{ verifyTarget.order_no }}</b></p>
        <p>顾客：{{ verifyTarget.customer_name || '—' }}（{{ verifyTarget.customer_phone }}）</p>
        <p>份数：{{ verifyTarget.quantity }} 份，金额 ¥{{ verifyTarget.total_amount }}</p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="核销码">
          <el-input v-model="verifyCode" maxlength="10" placeholder="顾客出示的 6 位核销码" style="width: 220px" @keyup.enter="handleVerify" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyVisible = false">取消</el-button>
        <el-button type="success" :loading="saving" @click="handleVerify">确认核销</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getOrders, verifyOrder } from '../api'

const statusText = { 1: '待自提', 2: '已完成', 3: '已取消', 4: '超时未取' }
const statusTagType = { 1: 'primary', 2: 'success', 3: 'info', 4: 'danger' }

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)

const filter = reactive({ status: null, pickup_date: '', keyword: '' })

const verifyVisible = ref(false)
const verifyTarget = ref(null)
const verifyCode = ref('')

function formatDate(d) {
  return d ? String(d).slice(0, 10) : ''
}

function formatDateTime(d) {
  return d ? String(d).slice(0, 19).replace('T', ' ') : ''
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (filter.status !== null && filter.status !== '') params.status = filter.status
    if (filter.pickup_date) params.pickup_date = filter.pickup_date
    if (filter.keyword) params.keyword = filter.keyword
    const data = await getOrders(params)
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openVerify(row) {
  verifyTarget.value = row
  verifyCode.value = ''
  verifyVisible.value = true
}

async function handleVerify() {
  if (!verifyCode.value.trim()) return ElMessage.warning('请输入核销码')
  saving.value = true
  try {
    await verifyOrder(verifyTarget.value.id, verifyCode.value.trim())
    ElMessage.success('核销成功，顾客可自提')
    verifyVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 10px; margin-bottom: 14px; }
.pagination { margin-top: 14px; justify-content: flex-end; }
.verify-code { font-family: monospace; font-weight: 800; letter-spacing: 2px; color: var(--green-700);
  background: var(--green-50); padding: 3px 8px; border-radius: 6px; }
.verify-order-info { background: var(--green-50); border-radius: 12px; padding: 14px 18px; margin-bottom: 16px; font-size: 14px; }
.verify-order-info p { margin: 6px 0; }
</style>
