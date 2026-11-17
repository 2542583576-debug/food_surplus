<template>
  <div class="page">
    <el-card shadow="never" class="tree-card">
      <template #header>
        <div class="card-header">
          <span>分类管理（拖拽节点可调整层级与排序）</span>
          <div>
            <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增根分类</el-button>
            <el-button :icon="Refresh" @click="loadTree">刷新</el-button>
          </div>
        </div>
      </template>

      <el-tree
        ref="treeRef"
        v-loading="loading"
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        draggable
        default-expand-all
        @node-drop="onNodeDrop"
      >
        <template #default="{ data }">
          <div class="node-row">
            <el-tag v-if="!data.is_enabled" size="small" type="info">已停用</el-tag>
            <span class="node-name">{{ data.name }}</span>
            <span class="node-actions" @click.stop>
              <el-button link type="primary" size="small" @click="openCreate(data)">+子分类</el-button>
              <el-button link type="success" size="small" @click="openTemplates(data)">属性模板</el-button>
              <el-button link type="warning" size="small" @click="openEdit(data)">编辑</el-button>
              <el-popconfirm title="确认删除该分类？（有子分类时将被拒绝）" @confirm="handleDelete(data)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </span>
          </div>
        </template>
      </el-tree>
      <el-empty v-if="!loading && treeData.length === 0" description="暂无分类，点击右上角新增" />
    </el-card>

    <!-- 新建/编辑分类 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑分类' : '新建分类'" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="父分类">
          <el-input :value="form.parent_name || '（根分类）'" disabled />
        </el-form-item>
        <el-form-item label="分类名称" required>
          <el-input v-model="form.name" maxlength="50" placeholder="如：面包 / 水果 / 甜品" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 属性模板管理 -->
    <el-dialog v-model="tplVisible" :title="`属性模板 - ${tplCategory?.name || ''}`" width="860px">
      <el-alert type="info" :closable="false" class="tpl-tip"
        title="属性模板定义该类商品需要填写的属性（如面包的克重、馅料）。商品创建时将按模板校验。" />
      <div class="tpl-list" v-loading="tplLoading">
        <div v-for="tpl in templates" :key="tpl.id" class="tpl-item">
          <div class="tpl-head">
            <b>{{ tpl.name }}</b>
            <span>
              <el-button link type="primary" size="small" @click="openTplEdit(tpl)">编辑</el-button>
              <el-popconfirm title="确认删除该模板？" @confirm="handleTplDelete(tpl)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </span>
          </div>
          <el-tag v-for="f in tpl.fields" :key="f.key" size="small" class="field-tag"
            :type="f.required ? 'danger' : 'info'">
            {{ f.label }}({{ typeText[f.type] }}){{ f.required ? '*' : '' }}
          </el-tag>
        </div>
        <el-empty v-if="!tplLoading && templates.length === 0" description="该分类暂无属性模板" :image-size="60" />
      </div>
      <template #footer>
        <el-button type="primary" :icon="Plus" @click="openTplEdit(null)">新增模板</el-button>
      </template>
    </el-dialog>

    <!-- 模板编辑器 -->
    <el-dialog v-model="tplFormVisible" :title="tplEditingId ? '编辑模板' : '新增模板'" width="760px" append-to-body>
      <el-form :model="tplForm" label-width="90px">
        <el-form-item label="模板名称" required>
          <el-input v-model="tplForm.name" maxlength="100" placeholder="如：面包基础属性" />
        </el-form-item>
        <el-form-item label="属性列表">
          <div class="fields-editor">
            <div v-for="(f, idx) in tplForm.fields" :key="idx" class="field-row">
              <el-input v-model="f.key" placeholder="key(英文)" style="width: 140px" />
              <el-input v-model="f.label" placeholder="名称" style="width: 120px" />
              <el-select v-model="f.type" style="width: 120px">
                <el-option v-for="t in Object.keys(typeText)" :key="t" :label="typeText[t]" :value="t" />
              </el-select>
              <el-input v-if="['select', 'multiselect'].includes(f.type)"
                :model-value="(f.options || []).join(',')"
                placeholder="选项,逗号分隔" style="width: 180px"
                @update:model-value="(v) => (f.options = v.split(',').map((s) => s.trim()).filter(Boolean))" />
              <el-checkbox v-model="f.required">必填</el-checkbox>
              <el-button link type="danger" :icon="Delete" @click="tplForm.fields.splice(idx, 1)" />
            </div>
            <el-button type="primary" plain size="small" :icon="Plus" @click="tplForm.fields.push({ key: '', label: '', type: 'text', required: false, options: [] })">
              添加属性
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tplFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleTplSave">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus, Refresh } from '@element-plus/icons-vue'
import {
  createCategory, createTemplate, deleteCategory, deleteTemplate,
  getCategoryTree, getTemplates, moveCategory, updateCategory, updateTemplate,
} from '../api'

const typeText = { text: '文本', number: '数字', select: '单选', multiselect: '多选', boolean: '是/否' }

const loading = ref(false)
const saving = ref(false)
const treeRef = ref()
const treeData = ref([])

// ---------- 分类 CRUD ----------
const formVisible = ref(false)
const editingId = ref(null)
const form = reactive({ parent_id: null, parent_name: '', name: '', sort_order: 0, is_enabled: true, remark: '' })

async function loadTree() {
  loading.value = true
  try {
    treeData.value = await getCategoryTree()
  } finally {
    loading.value = false
  }
}

function openCreate(parent) {
  editingId.value = null
  Object.assign(form, {
    parent_id: parent?.id ?? null,
    parent_name: parent?.name || '',
    name: '', sort_order: 0, is_enabled: true, remark: '',
  })
  formVisible.value = true
}

function openEdit(data) {
  editingId.value = data.id
  Object.assign(form, {
    parent_id: data.parent_id,
    parent_name: data.parent_id ? '（保持不变）' : '',
    name: data.name,
    sort_order: data.sort_order,
    is_enabled: data.is_enabled,
    remark: data.remark,
  })
  formVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) return ElMessage.warning('请填写分类名称')
  saving.value = true
  try {
    if (editingId.value) {
      await updateCategory(editingId.value, {
        name: form.name, sort_order: form.sort_order, is_enabled: form.is_enabled, remark: form.remark,
      })
    } else {
      await createCategory({
        parent_id: form.parent_id, name: form.name, sort_order: form.sort_order,
        is_enabled: form.is_enabled, remark: form.remark,
      })
    }
    ElMessage.success('保存成功')
    formVisible.value = false
    await loadTree()
  } finally {
    saving.value = false
  }
}

async function handleDelete(data) {
  await deleteCategory(data.id)
  ElMessage.success('删除成功')
  await loadTree()
}

// ---------- 拖拽移动 ----------
async function onNodeDrop(draggingNode, dropNode, dropType) {
  const node = draggingNode.data
  let parent_id = null
  let sort_order = node.sort_order
  if (dropType === 'inner') {
    parent_id = dropNode.data.id
    sort_order = (dropNode.data.children?.length || 0) - 1
  } else {
    parent_id = dropNode.data.parent_id
    sort_order = dropNode.data.sort_order
  }
  try {
    await moveCategory(node.id, { parent_id, sort_order })
    ElMessage.success('已移动')
  } catch {
    await loadTree() // 后端拒绝（循环引用等）时回刷恢复
  }
}

// ---------- 属性模板 ----------
const tplVisible = ref(false)
const tplLoading = ref(false)
const tplCategory = ref(null)
const templates = ref([])

const tplFormVisible = ref(false)
const tplEditingId = ref(null)
const tplForm = reactive({ name: '', fields: [] })

async function openTemplates(data) {
  tplCategory.value = data
  tplVisible.value = true
  tplLoading.value = true
  try {
    templates.value = await getTemplates(data.id)
  } finally {
    tplLoading.value = false
  }
}

function openTplEdit(tpl) {
  tplEditingId.value = tpl?.id ?? null
  tplForm.name = tpl?.name || ''
  tplForm.fields = tpl ? JSON.parse(JSON.stringify(tpl.fields)) : []
  tplFormVisible.value = true
}

async function handleTplSave() {
  if (!tplForm.name.trim()) return ElMessage.warning('请填写模板名称')
  if (tplForm.fields.length === 0) return ElMessage.warning('至少添加一个属性')
  for (const f of tplForm.fields) {
    if (!/^[a-zA-Z0-9_]+$/.test(f.key)) return ElMessage.warning(`属性 key「${f.key || '空'}」只能是英文/数字/下划线`)
    if (!f.label.trim()) return ElMessage.warning('属性名称不能为空')
    if (['select', 'multiselect'].includes(f.type) && (f.options || []).length === 0) {
      return ElMessage.warning(`「${f.label}」为选择类型，请填写选项`)
    }
  }
  saving.value = true
  try {
    if (tplEditingId.value) {
      await updateTemplate(tplEditingId.value, { name: tplForm.name, fields: tplForm.fields })
    } else {
      await createTemplate({ category_id: tplCategory.value.id, name: tplForm.name, fields: tplForm.fields })
    }
    ElMessage.success('模板已保存')
    tplFormVisible.value = false
    templates.value = await getTemplates(tplCategory.value.id)
  } finally {
    saving.value = false
  }
}

async function handleTplDelete(tpl) {
  await deleteTemplate(tpl.id)
  ElMessage.success('模板已删除')
  templates.value = await getTemplates(tplCategory.value.id)
}

onMounted(loadTree)
</script>

<style scoped>
.page { padding: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.node-row { display: flex; align-items: center; gap: 6px; flex: 1; padding-right: 8px; }
.node-name { font-size: 14px; }
.node-actions { margin-left: auto; display: none; }
:deep(.el-tree-node__content:hover) .node-actions { display: inline-flex; }
.tpl-tip { margin-bottom: 12px; }
.tpl-item { border: 1px solid #ebeef5; border-radius: 6px; padding: 12px; margin-bottom: 10px; }
.tpl-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.field-tag { margin-right: 6px; margin-bottom: 4px; }
.fields-editor { width: 100%; }
.field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
</style>
