<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>商品管理</span>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建商品</el-button>
        </div>
      </template>

      <div class="filters">
        <el-tree-select
          v-model="filter.category_id"
          :data="categoryTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          check-strictly
          clearable
          placeholder="全部分类"
          style="width: 200px"
        />
        <el-input v-model="filter.keyword" placeholder="商品名称" clearable style="width: 200px" @keyup.enter="load" />
        <el-select v-model="filter.is_on_sale" placeholder="上架状态" clearable style="width: 140px">
          <el-option label="在售" :value="true" />
          <el-option label="停售" :value="false" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="商品名称" min-width="160" />
        <el-table-column label="当日原价" width="100">
          <template #default="{ row }">¥{{ row.original_price }}</template>
        </el-table-column>
        <el-table-column label="属性" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="(v, k) in row.attributes" :key="k" size="small" type="info" class="attr-tag">
              {{ k }}: {{ v }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="在售" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_on_sale ? 'success' : 'info'" size="small">{{ row.is_on_sale ? '在售' : '停售' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该商品？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="load"
      />
    </el-card>

    <!-- 新建/编辑商品 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑商品' : '新建商品'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属分类" required>
          <el-tree-select
            v-model="form.category_id"
            :data="categoryTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            check-strictly
            placeholder="选择分类（决定属性模板）"
            style="width: 100%"
            @change="onCategoryChange"
          />
        </el-form-item>
        <el-form-item label="商品名称" required>
          <el-input v-model="form.name" maxlength="100" placeholder="如：全麦红豆吐司" />
        </el-form-item>
        <el-form-item label="当日原价">
          <el-input-number v-model="form.original_price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="主图URL">
          <el-input v-model="form.image" placeholder="选填" />
        </el-form-item>
        <el-form-item label="是否在售">
          <el-switch v-model="form.is_on_sale" />
        </el-form-item>

        <el-divider content-position="left">分类属性（按模板填写）</el-divider>
        <template v-if="tplFields.length > 0">
          <el-form-item v-for="f in tplFields" :key="f.key" :label="f.label" :required="f.required">
            <el-switch v-if="f.type === 'boolean'" v-model="form.attributes[f.key]" />
            <el-input-number v-else-if="f.type === 'number'" v-model="form.attributes[f.key]" />
            <el-select v-else-if="f.type === 'select'" v-model="form.attributes[f.key]" clearable style="width: 100%">
              <el-option v-for="o in f.options" :key="o" :label="o" :value="o" />
            </el-select>
            <el-select v-else-if="f.type === 'multiselect'" v-model="form.attributes[f.key]" multiple style="width: 100%">
              <el-option v-for="o in f.options" :key="o" :label="o" :value="o" />
            </el-select>
            <el-input v-else v-model="form.attributes[f.key]" />
          </el-form-item>
        </template>
        <el-alert
          v-else-if="form.category_id"
          type="info" :closable="false"
          title="该分类暂无属性模板，商品无需填写额外属性"
        />
        <el-alert v-else type="warning" :closable="false" title="请先选择分类，将按分类模板加载属性表单" />
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
import { Plus, Search } from '@element-plus/icons-vue'
import { createProduct, deleteProduct, getCategoryTree, getProducts, getTemplates, updateProduct } from '../api'

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const categoryTree = ref([])

const filter = reactive({ category_id: null, keyword: '', is_on_sale: null })

// ---------- 表单 ----------
const formVisible = ref(false)
const editingId = ref(null)
const tplFields = ref([]) // 当前分类模板字段
const form = reactive({
  category_id: null, name: '', original_price: 0, description: '', image: '',
  is_on_sale: true, attributes: {},
})

async function load() {
  loading.value = true
  try {
    const data = await getProducts({ page: page.value, size: size.value, ...cleanFilter() })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function cleanFilter() {
  const f = {}
  if (filter.category_id != null) f.category_id = filter.category_id
  if (filter.keyword) f.keyword = filter.keyword
  if (filter.is_on_sale !== null && filter.is_on_sale !== '') f.is_on_sale = filter.is_on_sale
  return f
}

async function loadCategories() {
  categoryTree.value = await getCategoryTree()
}

async function loadTplFields(categoryId) {
  tplFields.value = []
  form.attributes = {}
  if (!categoryId) return
  const templates = await getTemplates(categoryId)
  tplFields.value = templates.flatMap((t) => t.fields)
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    category_id: null, name: '', original_price: 0, description: '',
    image: '', is_on_sale: true, attributes: {},
  })
  tplFields.value = []
  formVisible.value = true
}

async function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    category_id: row.category_id,
    name: row.name,
    original_price: row.original_price,
    description: row.description,
    image: row.image,
    is_on_sale: row.is_on_sale,
    attributes: { ...(row.attributes || {}) },
  })
  await loadTplFields(row.category_id)
  // 保留已有属性值
  Object.assign(form.attributes, row.attributes || {})
  formVisible.value = true
}

async function onCategoryChange(categoryId) {
  await loadTplFields(categoryId)
}

async function handleSave() {
  if (!form.category_id) return ElMessage.warning('请选择分类')
  if (!form.name.trim()) return ElMessage.warning('请填写商品名称')
  // 本地必填校验
  for (const f of tplFields.value) {
    const v = form.attributes[f.key]
    if (f.required && (v === undefined || v === null || v === '' || (Array.isArray(v) && v.length === 0))) {
      return ElMessage.warning(`属性「${f.label}」为必填项`)
    }
  }
  saving.value = true
  try {
    const payload = {
      category_id: form.category_id, name: form.name, original_price: form.original_price,
      description: form.description, image: form.image, is_on_sale: form.is_on_sale,
      attributes: form.attributes,
    }
    if (editingId.value) {
      await updateProduct(editingId.value, payload)
    } else {
      await createProduct(payload)
    }
    ElMessage.success('保存成功')
    formVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await deleteProduct(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadCategories()])
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 10px; margin-bottom: 14px; }
.attr-tag { margin-right: 6px; margin-bottom: 4px; }
.pagination { margin-top: 14px; justify-content: flex-end; }
</style>
