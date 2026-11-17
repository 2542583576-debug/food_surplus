<template>
  <div class="page-wrap">
    <div class="section-head">
      <div>
        <h2 class="section-title">自提门店 🏪</h2>
        <p class="section-sub">预订后，请到以下门店出示核销码领取你的魔法袋</p>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col v-for="store in stores" :key="store.id" :xs="24" :sm="12" :md="8" class="col-item">
        <div class="store-card soft-card fade-up">
          <div class="store-cover">
            <span class="store-emoji">🏪</span>
            <el-tag v-if="store.bag_count > 0" type="success" effect="dark" round class="store-tag">
              {{ store.bag_count }} 款在售
            </el-tag>
            <el-tag v-else type="info" effect="dark" round class="store-tag">暂时领完</el-tag>
          </div>
          <div class="store-info">
            <h3>{{ store.store_name }}</h3>
            <div class="info-row"><el-icon><Location /></el-icon><span>{{ store.address }}</span></div>
            <div class="info-row"><el-icon><Clock /></el-icon><span>营业时间 {{ store.business_hours }}</span></div>
            <div class="info-row"><el-icon><Phone /></el-icon><span>{{ store.phone }}</span></div>
            <div class="store-actions">
              <el-button size="small" type="primary" plain @click="copyAddress(store)">
                <el-icon><DocumentCopy /></el-icon> 复制地址
              </el-button>
              <el-button size="small" type="success" plain @click="navigate(store)">
                <el-icon><Navigation /></el-icon> 导航前往
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && stores.length === 0" description="暂无门店信息" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getStores } from '../api/magic'

const loading = ref(false)
const stores = ref([])

async function load() {
  loading.value = true
  try {
    stores.value = await getStores()
  } finally {
    loading.value = false
  }
}

async function copyAddress(store) {
  try {
    await navigator.clipboard.writeText(`${store.store_name} ${store.address}`)
    ElMessage.success('地址已复制')
  } catch (e) {
    ElMessage.info(`地址：${store.address}`)
  }
}

function navigate(store) {
  const name = encodeURIComponent(store.store_name + store.address)
  // 使用高德地图网页版搜索，避免自绘地图
  window.open(`https://uri.amap.com/search?keyword=${name}`, '_blank')
}

onMounted(load)
</script>

<style scoped>
.section-head { margin-bottom: 20px; }
.col-item { margin-bottom: 20px; }
.store-card { overflow: hidden; transition: all 0.25s; }
.store-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.store-cover {
  position: relative; height: 120px;
  background: linear-gradient(135deg, #e4f5e9, #b9e6c6);
  display: flex; align-items: center; justify-content: center;
}
.store-emoji { font-size: 64px; }
.store-tag { position: absolute; top: 12px; right: 12px; }
.store-info { padding: 16px 18px 18px; }
.store-info h3 { margin: 0 0 12px; font-size: 17px; color: var(--ink); }
.info-row {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 13px; color: var(--ink-soft); margin-bottom: 9px; line-height: 1.5;
}
.info-row .el-icon { margin-top: 2px; color: var(--green-500); flex-shrink: 0; }
.store-actions { display: flex; gap: 8px; margin-top: 14px; }
.store-actions .el-button { flex: 1; margin: 0; }
</style>
