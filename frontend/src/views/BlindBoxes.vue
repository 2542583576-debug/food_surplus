<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>盲盒管理</span>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建盲盒</el-button>
        </div>
      </template>

      <div class="filters">
        <el-select v-model="filter.status" placeholder="全部状态" clearable style="width: 140px">
          <el-option v-for="(text, s) in statusText" :key="s" :label="text" :value="Number(s)" />
        </el-select>
        <el-date-picker v-model="filter.pickup_date" type="date" placeholder="自提日期" value-format="YYYY-MM-DD" clearable style="width: 160px" />
        <el-button type="primary" :icon="Search" @click="load">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="盲盒标题" min-width="150" />
        <el-table-column label="售价 / 总价值" width="130">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold">¥{{ row.price }}</span>
            <span style="color: #909399; font-size: 12px"> / ¥{{ row.total_value }}</span>
          </template>
        </el-table-column>
        <el-table-column label="库存" width="110">
          <template #default="{ row }">
            <el-progress :percentage="stockPercent(row)" :stroke-width="14" :show-text="false"
              :status="row.sold_count >= row.total_stock ? 'success' : undefined" style="width: 70px" />
            <span style="font-size: 12px; margin-left: 4px">{{ row.sold_count }}/{{ row.total_stock }}</span>
          </template>
        </el-table-column>
        <el-table-column label="自提时间" width="200">
          <template #default="{ row }">
            {{ formatDate(row.pickup_date) }} {{ row.pickup_start }} - {{ row.pickup_end }}
          </template>
        </el-table-column>
        <el-table-column label="内含商品" min-width="150">
          <template #default="{ row }">
            <el-tooltip v-if="row.items.length" placement="top">
              <template #content>
                <div v-for="it in row.items" :key="it.product_id">· {{ productName(it.product_id) }} × {{ it.quantity }}</div>
              </template>
              <span>{{ row.items.length }} 种商品</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status]" size="small">{{ statusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 0 || row.status === 2" link type="success" size="small" @click="handleStatus(row, 'on_sale')">上架</el-button>
            <el-button v-if="row.status === 1" link type="warning" size="small" @click="handleStatus(row, 'off_sale')">下架</el-button>
            <el-button v-if="row.status !== 1" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm v-if="row.status !== 1" title="确认删除该盲盒？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page" v-model:page-size="size" :total="total"
        :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        class="pagination" @change="load"
      />
    </el-card>

    <!-- 新建/编辑盲盒 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑盲盒' : '新建盲盒'" width="720px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="盲盒标题" required>
          <el-input v-model="form.title" maxlength="100" placeholder="如：面包惊喜盒（3件）" />
        </el-form-item>
        <el-form-item label="售价 ¥" required>
          <el-input-number v-model="form.price" :min="0.01" :precision="2" />
          <span class="tip">售价建议低于商品总价值，体现"捡漏"优惠</span>
        </el-form-item>
        <el-form-item label="总价值 ¥">
          <el-input-number v-model="form.total_value" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="投放数量" required>
          <el-input-number v-model="form.total_stock" :min="1" :max="9999" />
          <span class="tip">当日限量份数</span>
        </el-form-item>
        <el-form-item label="自提日期" required>
          <el-date-picker v-model="form.pickup_date" type="date" value-format="YYYY-MM-DD" :disabled-date="(d) => d.getTime() < Date.now() - 86400000" />
        </el-form-item>
        <el-form-item label="自提时段" required>
          <el-time-select v-model="form.pickup_start" start="06:00" end="23:00" step="00:30" style="width: 130px" />
          <span class="tip"> 至 </span>
          <el-time-select v-model="form.pickup_end" start="06:00" end="23:00" step="00:30" :min-time="form.pickup_start" style="width: 130px" />
        </el-form-item>
        <el-form-item label="内含商品" required>
          <div class="items-editor">
            <div v-for="(it, idx) in form.items" :key="idx" class="item-row">
              <el-select v-model="it.product_id" filterable placeholder="选择商品" style="width: 320px">
                <el-option v-for="p in products" :key="p.id" :label="`${p.name}（¥${p.original_price}）`" :value="p.id" />
              </el-select>
              <el-input-number v-model="it.quantity" :min="1" :max="99" controls-position="right" style="width: 110px" />
              <span class="tip">份</span>
              <el-button link type="danger" :icon="Delete" @click="form.items.splice(idx, 1)" />
            </div>
            <el-button type="primary" plain size="small" :icon="Plus" @click="form.items.push({ product_id: null, quantity: 1 })">
              添加商品
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" placeholder="如：内含当日现烤余量面包，可能含临期品，介意慎拍" />
        </el-form-item>
        <el-form-item label="推荐位">
          <el-switch v-model="form.is_featured" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus, Search } from '@element-plus/icons-vue'
import {
  changeBlindBoxStatus, createBlindBox, deleteBlindBox, getBlindBoxes,
  getProducts, updateBlindBox,
} from '../api'

const statusText = { 0: '草稿', 1: '已上架', 2: '已下架', 3: '售罄' }
const statusTagType = { 0: 'info', 1: 'success', 2: 'warning', 3: 'danger' }

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const products = ref([]) // 商品下拉数据

const filter = reactive({ status: null, pickup_date: '' })

const formVisible = ref(false)
const editingId = ref(null)
const form = reactive({
  title: '', price: null, total_value: 0, total_stock: 10,
  pickup_date: '', pickup_start: '18:00', pickup_end: '21:00',
  items: [{ product_id: null, quantity: 1 }],
  description: '', is_featured: false,
})

function productName(pid) {
  return products.value.find((p) => p.id === pid)?.name || `#${pid}`
}

function stockPercent(row) {
  return row.total_stock > 0 ? Math.round((row.sold_count / row.total_stock) * 100) : 0
}

function formatDate(d) {
  return d ? String(d).slice(0, 10) : ''
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (filter.status !== null && filter.status !== '') params.status = filter.status
    if (filter.pickup_date) params.pickup_date = filter.pickup_date
    const data = await getBlindBoxes(params)
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  const data = await getProducts({ page: 1, size: 100, is_on_sale: true })
  products.value = data.items
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    title: '', price: null, total_value: 0, total_stock: 10,
    pickup_date: '', pickup_start: '18:00', pickup_end: '21:00',
    items: [{ product_id: null, quantity: 1 }],
    description: '', is_featured: false,
  })
  formVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    title: row.title,
    price: row.price,
    total_value: row.total_value,
    total_stock: row.total_stock,
    pickup_date: formatDate(row.pickup_date),
    pickup_start: row.pickup_start,
    pickup_end: row.pickup_end,
    items: row.items.map((it) => ({ product_id: it.product_id, quantity: it.quantity })),
    description: row.description,
    is_featured: row.is_featured,
  })
  formVisible.value = true
}

async function handleSave() {
  if (!form.title.trim()) return ElMessage.warning('请填写盲盒标题')
  if (!form.price || form.price <= 0) return ElMessage.warning('请填写售价')
  if (!form.pickup_date) return ElMessage.warning('请选择自提日期')
  if (!form.pickup_start || !form.pickup_end) return ElMessage.warning('请选择自提时段')
  if (form.pickup_start >= form.pickup_end) return ElMessage.warning('自提开始时间必须早于截止时间')
  const validItems = form.items.filter((it) => it.product_id && it.quantity > 0)
  if (validItems.length === 0) return ElMessage.warning('至少添加一种商品')
  saving.value = true
  try {
    const payload = { ...form, items: validItems, price: Number(form.price), total_value: Number(form.total_value) }
    if (editingId.value) {
      await updateBlindBox(editingId.value, payload)
    } else {
      await createBlindBox(payload)
    }
    ElMessage.success('保存成功')
    formVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleStatus(row, action) {
  await changeBlindBoxStatus(row.id, action)
  ElMessage.success(action === 'on_sale' ? '已上架' : '已下架')
  await load()
}

async function handleDelete(row) {
  await deleteBlindBox(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadProducts()])
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 10px; margin-bottom: 14px; }
.pagination { margin-top: 14px; justify-content: flex-end; }
.tip { color: #909399; font-size: 12px; margin: 0 8px; }
.items-editor { width: 100%; }
.item-row { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
</style>
