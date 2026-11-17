<template>
  <div class="page-wrap">
    <div class="section-head">
      <div>
        <h2 class="section-title">我的订单</h2>
        <p class="section-sub">在这里查看核销码，到店出示即可领取魔法袋</p>
      </div>
      <el-button type="primary" plain @click="$router.push('/bags')">
        <el-icon><Plus /></el-icon> 再领一袋
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="order-tabs">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待自提" name="1" />
      <el-tab-pane label="已完成" name="2" />
      <el-tab-pane label="已取消/超时" name="cancel" />
    </el-tabs>

    <div v-if="filteredOrders.length" class="order-list">
      <div v-for="order in filteredOrders" :key="order.id" class="order-card fade-up">
        <div class="order-top">
          <div class="order-store">
            <span class="store-icon">🏪</span>
            <div>
              <div class="store-name">余量魔法袋</div>
              <div class="order-no">订单号 {{ order.order_no }}</div>
            </div>
          </div>
          <el-tag :type="statusTag[order.status]" effect="light" round size="large">
            {{ statusText[order.status] }}
          </el-tag>
        </div>

        <div class="order-body">
          <div class="order-main">
            <div class="order-detail-row">
              <span>实付金额</span>
              <strong class="amount">¥{{ order.pay_amount }}</strong>
            </div>
            <div class="order-detail-row">
              <span>支付方式</span>
              <span>{{ order.pay_method === 'store' ? '到店付款' : '在线支付' }}</span>
            </div>
            <div class="order-detail-row">
              <span>自提日期</span>
              <span>{{ order.pickup_date || '当日' }}</span>
            </div>
            <div class="order-detail-row">
              <span>下单时间</span>
              <span>{{ formatTime(order.create_time) }}</span>
            </div>
          </div>

          <!-- 待自提：展示核销码 -->
          <div v-if="order.status === 1" class="code-panel">
            <div class="code-label">到店出示此核销码</div>
            <div class="code-value">{{ order.verify_code }}</div>
            <div class="code-hint">请妥善保存，领取时交给店员</div>
          </div>
          <!-- 已完成：碳减排徽章 -->
          <div v-else-if="order.status === 2" class="done-panel">
            <div class="done-icon">🌍</div>
            <div>已为地球减少约 <strong>1.2 kg</strong> 碳排放</div>
          </div>
          <div v-else class="done-panel">
            <div class="done-icon">📦</div>
            <div>该订单已结束</div>
          </div>
        </div>

        <div class="order-bottom">
          <span class="order-phone">📱 {{ order.customer_phone || '—' }}</span>
          <el-button v-if="order.status === 1" size="small" type="danger" plain
                     @click="handleCancel(order)">取消订单</el-button>
        </div>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="还没有订单，去魔法袋广场领一袋吧">
      <el-button type="primary" @click="$router.push('/bags')">去逛逛</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyOrders, cancelOrder } from '../api/magic'

const loading = ref(false)
const orders = ref([])
const activeTab = ref('all')
const statusText = { 1: '待自提', 2: '已完成', 3: '已取消', 4: '已超时' }
const statusTag = { 1: 'primary', 2: 'success', 3: 'info', 4: 'warning' }

const filteredOrders = computed(() => {
  if (activeTab.value === 'all') return orders.value
  if (activeTab.value === 'cancel') return orders.value.filter((o) => o.status === 3 || o.status === 4)
  return orders.value.filter((o) => o.status === Number(activeTab.value))
})

function formatTime(value) {
  return value ? String(value).slice(0, 16).replace('T', ' ') : ''
}

async function load() {
  loading.value = true
  try {
    orders.value = await getMyOrders()
  } finally {
    loading.value = false
  }
}

async function handleCancel(order) {
  try {
    await ElMessageBox.confirm('确定要取消这个订单吗？取消后库存将释放。', '提示', {
      type: 'warning', confirmButtonText: '确定取消', cancelButtonText: '再想想',
    })
    await cancelOrder(order.order_no, order.customer_phone || '')
    ElMessage.success('订单已取消')
    await load()
  } catch (e) {
    // 用户取消操作，忽略
  }
}

onMounted(load)
</script>

<style scoped>
.section-head { display: flex; justify-content: space-between; align-items: flex-end; }
.order-tabs :deep(.el-tabs__header) { margin-bottom: 20px; }
.order-list { display: flex; flex-direction: column; gap: 16px; }
.order-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.order-top {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  background: var(--green-50);
  border-bottom: 1px solid var(--line);
}
.order-store { display: flex; align-items: center; gap: 10px; }
.store-icon { font-size: 26px; }
.store-name { font-size: 15px; font-weight: 700; color: var(--ink); }
.order-no { font-size: 11px; color: var(--ink-mute); margin-top: 2px; }
.order-body { display: flex; gap: 20px; padding: 20px; }
.order-main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 12px 24px; }
.order-detail-row { display: flex; flex-direction: column; gap: 2px; font-size: 13px; }
.order-detail-row span:first-child { color: var(--ink-mute); font-size: 11px; }
.order-detail-row span:last-child { color: var(--ink); }
.order-detail-row .amount { color: #e8503a; font-size: 20px; font-weight: 800; }
.code-panel {
  width: 210px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--green-50), #e6f5ea);
  border: 2px dashed var(--green-400);
  border-radius: 14px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 14px;
}
.code-label { font-size: 11px; color: var(--green-700); margin-bottom: 6px; }
.code-value { font-size: 32px; font-weight: 800; letter-spacing: 5px; color: var(--green-700); }
.code-hint { font-size: 10px; color: var(--ink-mute); margin-top: 6px; }
.done-panel {
  width: 210px; flex-shrink: 0;
  background: var(--green-50); border-radius: 14px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 14px; text-align: center;
  font-size: 12px; color: var(--ink-soft);
}
.done-panel strong { color: var(--green-600); }
.done-icon { font-size: 32px; }
.order-bottom {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-top: 1px solid var(--line);
}
.order-phone { font-size: 12px; color: var(--ink-mute); }
@media (max-width: 760px) {
  .order-body { flex-direction: column; }
  .code-panel, .done-panel { width: 100%; }
  .order-main { grid-template-columns: 1fr; }
}
</style>
