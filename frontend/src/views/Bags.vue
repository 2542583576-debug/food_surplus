<template>
  <div class="bags-page">
    <!-- Hero 横幅 -->
    <section class="hero fade-up">
      <div class="hero-content">
        <div class="hero-badge">🌍 珍惜食物 · 低碳生活</div>
        <h1>今天，来打开一袋<span>惊喜</span>吧</h1>
        <p class="hero-lead">
          商家把当天依然新鲜、却卖不完的食物装进"魔法袋"，超值出售。<br>
          你用更少的钱收获美味，也让这些食物免于被浪费。
        </p>
        <div class="hero-stats">
          <div class="hero-stat">
            <strong>{{ platform.total_save_food || 0 }}<small> kg</small></strong>
            <span>已拯救食物</span>
          </div>
          <div class="hero-stat">
            <strong>{{ platform.total_order_count || 0 }}<small> 份</small></strong>
            <span>魔法袋被领取</span>
          </div>
          <div class="hero-stat">
            <strong>{{ platform.total_reduce_carbon || 0 }}<small> kg</small></strong>
            <span>减少碳排放</span>
          </div>
        </div>
      </div>
      <div class="hero-art">
        <div class="bag-illustration">
          <div class="paper-bag">🛍️</div>
          <span class="float float-1">🥐</span>
          <span class="float float-2">🍞</span>
          <span class="float float-3">🍎</span>
          <span class="float float-4">🧁</span>
        </div>
      </div>
    </section>

    <!-- 三步玩法 -->
    <section class="how-it-works fade-up">
      <div class="step" v-for="(step, i) in steps" :key="i">
        <div class="step-num">{{ i + 1 }}</div>
        <div class="step-icon">{{ step.icon }}</div>
        <div class="step-text">
          <h4>{{ step.title }}</h4>
          <p>{{ step.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 魔法袋列表 -->
    <section class="bags-section">
      <div class="section-head">
        <div>
          <h2 class="section-title">今日可领魔法袋</h2>
          <p class="section-sub">数量有限，先到先得 · 点击卡片即可预订</p>
        </div>
        <el-tag type="success" effect="light" round size="large">共 {{ bags.length }} 款在售</el-tag>
      </div>

      <el-row :gutter="20">
        <el-col v-for="bag in bags" :key="bag.id" :xs="24" :sm="12" :md="8" class="col-item">
          <div class="bag-card" :class="{ soldout: bag.stock <= 0 }" @click="openOrder(bag)">
            <div class="bag-cover">
              <img v-if="bag.cover" :src="bag.cover" :alt="bag.bag_name" />
              <div v-else class="cover-placeholder" :style="coverStyle(bag.id)">
                <span>{{ bagEmoji(bag) }}</span>
              </div>
              <span class="discount-badge">省 ¥{{ discount(bag) }}</span>
              <span v-if="bag.stock <= 0" class="soldout-mask">已售罄</span>
            </div>
            <div class="bag-info">
              <h3>{{ bag.bag_name }}</h3>
              <p class="bag-desc">{{ bag.description || '当日新鲜余量食物组合，具体以门店为准' }}</p>
              <div class="price-row">
                <div class="price-now"><small>¥</small>{{ bag.sale_price }}</div>
                <div class="price-origin">¥{{ bag.original_price }}</div>
                <div class="price-off">{{ discountPercent(bag) }}折</div>
              </div>
              <div class="bag-meta">
                <span><el-icon><Clock /></el-icon> {{ bag.pick_start_time }}–{{ bag.pick_end_time }}</span>
                <span :class="{ 'stock-low': bag.stock <= 3 }"><el-icon><Box /></el-icon> 剩 {{ bag.stock }} 份</span>
              </div>
              <el-button class="order-btn" :type="bag.stock > 0 ? 'primary' : 'info'" block
                         :disabled="bag.stock <= 0">
                {{ bag.stock > 0 ? '立即预订' : '已售罄' }}
                <el-icon v-if="bag.stock > 0"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-empty v-if="!loading && bags.length === 0" description="今日魔法袋已被领完，明天早点来看看哦" />
    </section>

    <!-- 预订弹窗 -->
    <el-dialog v-model="dialogVisible" width="460px" :show-close="!lastOrder" class="order-dialog">
      <template #header>
        <div class="dialog-title">
          <span v-if="!lastOrder">🎁 预订魔法袋</span>
          <span v-else>🎉 预订成功</span>
        </div>
      </template>

      <!-- 下单表单 -->
      <template v-if="currentBag && !lastOrder">
        <div class="order-summary">
          <div class="order-summary-icon">{{ bagEmoji(currentBag) }}</div>
          <div class="order-summary-info">
            <h4>{{ currentBag.bag_name }}</h4>
            <p>{{ currentBag.description || '当日新鲜余量食物组合' }}</p>
            <div class="order-price"><strong>¥{{ currentBag.sale_price }}</strong> <s>¥{{ currentBag.original_price }}</s></div>
          </div>
        </div>
        <div class="order-notice">
          <el-icon><InfoFilled /></el-icon>
          领取时段 {{ currentBag.pick_start_time }}–{{ currentBag.pick_end_time }}，请在时段内到店自提
        </div>
        <el-form label-position="top" class="order-form">
          <el-form-item label="联系手机号">
            <el-input v-model="phone" maxlength="20" placeholder="用于到店核销，请填写正确手机号">
              <template #prefix><el-icon><Iphone /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item label="你的称呼（选填）">
            <el-input v-model="customerName" maxlength="20" placeholder="例如：张先生">
              <template #prefix><el-icon><EditPen /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item label="支付方式">
            <el-radio-group v-model="payMethod">
              <el-radio value="store">到店付款</el-radio>
              <el-radio value="online">在线支付</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </template>

      <!-- 成功结果 -->
      <template v-if="lastOrder">
        <div class="success-view">
          <div class="success-icon">✓</div>
          <h3>预订成功，等你来取！</h3>
          <p>请到店出示下方核销码，交给店员即可领取</p>
          <div class="verify-code">{{ lastOrder.verify_code }}</div>
          <div class="verify-tip">📍 领取时段 {{ currentBag?.pick_start_time }}–{{ currentBag?.pick_end_time }}</div>
          <el-button type="primary" class="success-btn" @click="goOrders">查看我的订单</el-button>
        </div>
      </template>

      <template #footer>
        <el-button v-if="!lastOrder" @click="dialogVisible = false">取消</el-button>
        <el-button v-if="!lastOrder" type="primary" :loading="saving" @click="submitOrder">
          确认预订 · ¥{{ currentBag?.sale_price }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getBags, createOrder, getPlatformCarbon } from '../api/magic'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const bags = ref([])
const platform = ref({})
const dialogVisible = ref(false)
const currentBag = ref(null)
const lastOrder = ref(null)
const phone = ref('')
const customerName = ref('')
const payMethod = ref('store')

const steps = [
  { icon: '🔍', title: '挑选魔法袋', desc: '浏览今日余量，选你喜欢的' },
  { icon: '📱', title: '在线预订', desc: '填写手机号，立即锁定名额' },
  { icon: '🏪', title: '到店自提', desc: '出示核销码，领取你的惊喜' },
]

function bagEmoji(bag) {
  const text = (bag.bag_name || '') + (bag.description || '')
  if (/面包|烘焙|吐司|欧包/.test(text)) return '🥐'
  if (/水果|鲜果|轻食/.test(text)) return '🍎'
  if (/甜品|蛋糕|甜点/.test(text)) return '🧁'
  if (/熟食|饭菜|便当/.test(text)) return '🍱'
  if (/蔬菜|沙拉/.test(text)) return '🥗'
  return '🎁'
}

const coverThemes = [
  ['#fdf0dc', '#f7c98b'], ['#e4f5e9', '#9bdcb2'], ['#fdeaea', '#f4b3b3'],
  ['#e8f0fe', '#a9c6f5'], ['#f3eafe', '#cbb0f0'], ['#fff3e0', '#ffcc80'],
]
function coverStyle(id) {
  const [a, b] = coverThemes[(id || 0) % coverThemes.length]
  return { background: `linear-gradient(135deg, ${a}, ${b})` }
}
function discount(bag) {
  return (Number(bag.original_price || 0) - Number(bag.sale_price || 0)).toFixed(0)
}
function discountPercent(bag) {
  const o = Number(bag.original_price || 0)
  const s = Number(bag.sale_price || 0)
  if (!o) return '—'
  return (s / o * 10).toFixed(1)
}

async function load() {
  loading.value = true
  try {
    const [bagList, carbon] = await Promise.all([
      getBags({ page: 1, size: 50 }),
      getPlatformCarbon().catch(() => ({})),
    ])
    bags.value = bagList
    platform.value = carbon
  } finally {
    loading.value = false
  }
}

function openOrder(bag) {
  if (bag.stock <= 0) return
  currentBag.value = bag
  lastOrder.value = null
  phone.value = ''
  customerName.value = ''
  payMethod.value = 'store'
  dialogVisible.value = true
}

async function submitOrder() {
  if (!/^1[3-9]\d{9}$/.test(phone.value.trim())) {
    ElMessage.warning('请填写正确的 11 位手机号')
    return
  }
  saving.value = true
  try {
    lastOrder.value = await createOrder({
      bag_id: currentBag.value.id,
      customer_phone: phone.value.trim(),
      customer_name: customerName.value.trim(),
      pay_method: payMethod.value,
    })
    await load()
  } finally {
    saving.value = false
  }
}

function goOrders() {
  dialogVisible.value = false
  router.push('/my-orders')
}

onMounted(load)
</script>

<style scoped>
.bags-page { max-width: 1240px; margin: 0 auto; padding: 24px 28px 56px; }

/* Hero */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 300px;
  border-radius: 24px;
  padding: 44px 52px;
  overflow: hidden;
  background: linear-gradient(120deg, #eaf7ee 0%, #f3faf3 60%, #fdf3e3 100%);
  box-shadow: var(--shadow);
}
.hero-content { position: relative; z-index: 2; flex: 1; }
.hero-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(53, 168, 102, 0.12);
  color: var(--green-700);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 16px;
}
.hero h1 {
  font-size: 40px;
  line-height: 1.25;
  margin: 0 0 16px;
  color: var(--ink);
  letter-spacing: 1px;
}
.hero h1 span { color: var(--green-500); }
.hero-lead { font-size: 15px; line-height: 1.9; color: var(--ink-soft); margin: 0 0 26px; }
.hero-stats { display: flex; gap: 44px; }
.hero-stat { display: flex; flex-direction: column; }
.hero-stat strong { font-size: 28px; color: var(--green-600); }
.hero-stat strong small { font-size: 14px; font-weight: 500; }
.hero-stat span { font-size: 12px; color: var(--ink-mute); margin-top: 2px; }
.hero-art { position: relative; width: 280px; height: 220px; flex-shrink: 0; }
.bag-illustration { position: relative; width: 100%; height: 100%; }
.paper-bag { font-size: 150px; text-align: center; line-height: 220px; filter: drop-shadow(0 12px 16px rgba(0,0,0,0.12)); }
.float { position: absolute; font-size: 38px; animation: bob 3s ease-in-out infinite; }
.float-1 { top: 12px; left: 10px; }
.float-2 { top: 30px; right: 6px; animation-delay: 0.6s; }
.float-3 { bottom: 22px; left: 24px; animation-delay: 1.2s; }
.float-4 { bottom: 8px; right: 28px; animation-delay: 1.8s; font-size: 32px; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

/* 三步玩法 */
.how-it-works {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 20px 0 36px;
}
.step {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
}
.step-num {
  width: 26px; height: 26px; flex-shrink: 0;
  border-radius: 50%;
  background: var(--green-500);
  color: #fff;
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.step-icon { font-size: 30px; }
.step-text h4 { margin: 0 0 3px; font-size: 15px; color: var(--ink); }
.step-text p { margin: 0; font-size: 12px; color: var(--ink-mute); }

/* 列表 */
.section-head { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
.col-item { margin-bottom: 20px; }
.bag-card {
  height: 100%;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
}
.bag-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); border-color: var(--green-200); }
.bag-card.soldout { opacity: 0.72; cursor: not-allowed; }
.bag-cover { position: relative; height: 168px; overflow: hidden; }
.bag-cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.cover-placeholder span { font-size: 76px; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.1)); transition: transform 0.3s; }
.bag-card:hover .cover-placeholder span { transform: scale(1.12) rotate(-6deg); }
.discount-badge {
  position: absolute; top: 12px; left: 12px;
  background: linear-gradient(135deg, #f56c6c, #e8503a);
  color: #fff; font-size: 12px; font-weight: 700;
  padding: 4px 10px; border-radius: 10px;
  box-shadow: 0 4px 10px rgba(233, 90, 70, 0.3);
}
.soldout-mask {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.45);
  color: #fff; font-size: 20px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.bag-info { padding: 16px 18px 18px; display: flex; flex-direction: column; flex: 1; }
.bag-info h3 { margin: 0 0 6px; font-size: 17px; color: var(--ink); }
.bag-desc {
  margin: 0 0 12px; font-size: 12px; color: var(--ink-soft);
  line-height: 1.6; min-height: 38px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.price-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; }
.price-now { font-size: 26px; font-weight: 800; color: #e8503a; }
.price-now small { font-size: 14px; }
.price-origin { font-size: 13px; color: var(--ink-mute); text-decoration: line-through; }
.price-off { margin-left: auto; font-size: 12px; color: #e8503a; background: #fdeaea; padding: 2px 8px; border-radius: 8px; }
.bag-meta {
  display: flex; justify-content: space-between;
  font-size: 12px; color: var(--ink-mute); margin-bottom: 14px;
}
.bag-meta span { display: flex; align-items: center; gap: 3px; }
.bag-meta .stock-low { color: #e8503a; font-weight: 600; }
.order-btn { margin-top: auto; height: 40px; font-weight: 600; }

/* 弹窗 */
.dialog-title { font-size: 18px; font-weight: 700; color: var(--ink); }
.order-summary { display: flex; gap: 14px; padding: 14px; background: var(--green-50); border-radius: 14px; margin-bottom: 14px; }
.order-summary-icon { font-size: 48px; width: 64px; text-align: center; }
.order-summary-info h4 { margin: 0 0 4px; font-size: 16px; }
.order-summary-info p { margin: 0 0 8px; font-size: 12px; color: var(--ink-soft); }
.order-price strong { font-size: 22px; color: #e8503a; }
.order-price s { color: var(--ink-mute); margin-left: 6px; }
.order-notice {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--green-700);
  background: var(--green-50); padding: 8px 12px; border-radius: 10px; margin-bottom: 16px;
}
.order-form :deep(.el-form-item) { margin-bottom: 14px; }
.order-form :deep(.el-form-item__label) { font-size: 13px; color: var(--ink-soft); }

/* 成功页 */
.success-view { text-align: center; padding: 10px 0; }
.success-icon {
  width: 64px; height: 64px; margin: 0 auto 16px;
  border-radius: 50%; background: var(--green-100); color: var(--green-600);
  font-size: 36px; display: flex; align-items: center; justify-content: center;
}
.success-view h3 { margin: 0 0 6px; font-size: 20px; }
.success-view p { margin: 0 0 18px; font-size: 13px; color: var(--ink-soft); }
.verify-code {
  display: inline-block; font-size: 40px; font-weight: 800; letter-spacing: 8px;
  color: var(--green-700); background: var(--green-50);
  padding: 14px 28px; border-radius: 14px; border: 2px dashed var(--green-400);
}
.verify-tip { margin: 14px 0 20px; font-size: 13px; color: var(--ink-soft); }
.success-btn { width: 100%; height: 42px; }

@media (max-width: 900px) {
  .bags-page { padding: 16px; }
  .hero { flex-direction: column; padding: 32px 24px; }
  .hero h1 { font-size: 30px; }
  .hero-art { display: none; }
  .hero-stats { gap: 24px; }
  .how-it-works { grid-template-columns: 1fr; }
}
</style>
