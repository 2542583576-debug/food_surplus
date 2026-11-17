<template>
  <div class="page-wrap">
    <div class="section-head">
      <div>
        <h2 class="section-title">魔法袋管理</h2>
        <p class="section-sub">发布和管理你的余量魔法袋，让好食物遇见需要的人</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建魔法袋</el-button>
    </div>

    <div v-if="bags.length" class="bag-grid">
      <div v-for="bag in bags" :key="bag.id" class="admin-bag-card soft-card">
        <div class="admin-bag-cover">
          <img v-if="bag.cover" :src="bag.cover" :alt="bag.bag_name" />
          <div v-else class="cover-empty">📦</div>
          <el-tag :type="bag.status === 1 ? 'success' : 'info'" effect="dark" round class="status-tag">
            {{ bag.status === 1 ? '上架中' : '已下架' }}
          </el-tag>
        </div>
        <div class="admin-bag-body">
          <h3>{{ bag.bag_name }}</h3>
          <p class="admin-bag-desc">{{ bag.description || '暂无说明' }}</p>
          <div class="admin-bag-price">
            <strong>¥{{ bag.sale_price }}</strong>
            <s>¥{{ bag.original_price }}</s>
          </div>
          <div class="admin-bag-meta">
            <span>库存 {{ bag.stock }} 份</span>
            <span>{{ bag.pick_start_time }}–{{ bag.pick_end_time }}</span>
          </div>
          <div class="admin-bag-actions">
            <el-button size="small" type="primary" plain @click="openEdit(bag)">编辑</el-button>
            <el-popconfirm title="确认删除这个魔法袋？" @confirm="handleDelete(bag)">
              <template #reference>
                <el-button size="small" type="danger" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
    </div>
    <el-empty v-else-if="!loading" description="还没有魔法袋，点击右上角新建" />

    <el-dialog v-model="visible" :title="editingId ? '编辑魔法袋' : '新建魔法袋'" width="540px">
      <el-form :model="form" label-position="top" class="bag-form">
        <el-form-item label="魔法袋名称" required>
          <el-input v-model="form.bag_name" maxlength="100" placeholder="例如：傍晚面包惊喜袋" />
        </el-form-item>
        <el-form-item label="内容说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="里面有什么食物？例如：现烤面包 3-5 件" />
        </el-form-item>
        <el-form-item label="封面图片">
          <div class="upload-row">
            <el-upload
              class="cover-uploader"
              action="/api/upload/image"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeUpload"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
            >
              <img v-if="form.cover" :src="form.cover" class="cover-preview" />
              <div v-else class="cover-upload-box">
                <el-icon><Plus /></el-icon>
                <span>点击上传</span>
              </div>
            </el-upload>
            <div class="upload-tip">建议正方形图片，不超过 5MB<br>支持 jpg / png / webp / gif</div>
          </div>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="原价 (¥)" required>
              <el-input-number v-model="form.original_price" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="售价 (¥)" required>
              <el-input-number v-model="form.sale_price" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="库存份数" required>
          <el-input-number v-model="form.stock" :min="0" :max="9999" style="width:100%" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="领取开始" required>
              <el-time-select v-model="form.pick_start_time" start="06:00" end="23:30" step="00:30" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="领取结束" required>
              <el-time-select v-model="form.pick_end_time" start="06:00" end="23:30" step="00:30" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="立即上架">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getBags, createBag, updateBag, deleteBag } from '../api/magic'

const loading = ref(false)
const saving = ref(false)
const visible = ref(false)
const bags = ref([])
const editingId = ref(null)
const token = localStorage.getItem('token') || ''
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token}` }))

const emptyForm = () => ({
  bag_name: '', description: '', cover: '', original_price: 0, sale_price: 0,
  stock: 0, pick_start_time: '18:00', pick_end_time: '21:00', status: 1,
})
const form = reactive(emptyForm())

async function load() {
  loading.value = true
  try {
    bags.value = await getBags({ page: 1, size: 100 })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  visible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    bag_name: row.bag_name,
    description: row.description || '',
    cover: row.cover || '',
    original_price: Number(row.original_price),
    sale_price: Number(row.sale_price),
    stock: row.stock,
    pick_start_time: row.pick_start_time,
    pick_end_time: row.pick_end_time,
    status: row.status,
  })
  visible.value = true
}

function beforeUpload(file) {
  const ok = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)
  if (!ok) { ElMessage.error('仅支持 jpg/png/webp/gif 图片'); return false }
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('图片不能超过 5MB'); return false }
  return true
}
function handleUploadSuccess(res) {
  form.cover = res.url
  ElMessage.success('图片上传成功')
}
function handleUploadError() {
  ElMessage.error('图片上传失败，请重试')
}

async function submit() {
  if (!form.bag_name) return ElMessage.warning('请填写魔法袋名称')
  if (form.sale_price > form.original_price) return ElMessage.warning('售价不能高于原价')
  saving.value = true
  try {
    if (editingId.value) {
      await updateBag(editingId.value, form)
    } else {
      await createBag(form)
    }
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await deleteBag(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.section-head { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
.bag-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }
.admin-bag-card { overflow: hidden; transition: all 0.25s; }
.admin-bag-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.admin-bag-cover { position: relative; height: 140px; background: linear-gradient(135deg, #e4f5e9, #b9e6c6); }
.admin-bag-cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-empty { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 52px; }
.status-tag { position: absolute; top: 10px; right: 10px; }
.admin-bag-body { padding: 14px 16px 16px; }
.admin-bag-body h3 { margin: 0 0 6px; font-size: 16px; }
.admin-bag-desc { margin: 0 0 10px; font-size: 12px; color: var(--ink-soft); min-height: 34px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.admin-bag-price strong { color: #e8503a; font-size: 20px; }
.admin-bag-price s { color: var(--ink-mute); margin-left: 8px; font-size: 12px; }
.admin-bag-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-mute); margin: 10px 0 12px; }
.admin-bag-actions { display: flex; gap: 8px; }
.admin-bag-actions .el-button { flex: 1; margin: 0; }
.bag-form :deep(.el-form-item) { margin-bottom: 16px; }
.upload-row { display: flex; align-items: center; gap: 16px; }
.cover-preview { width: 90px; height: 90px; object-fit: cover; border-radius: 10px; }
.cover-upload-box { width: 90px; height: 90px; border: 1px dashed var(--green-400); border-radius: 10px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: var(--green-600); gap: 4px; background: var(--green-50); cursor: pointer; font-size: 12px; }
.upload-tip { font-size: 12px; color: var(--ink-mute); line-height: 1.7; }
</style>
