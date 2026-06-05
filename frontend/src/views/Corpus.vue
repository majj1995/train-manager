<template>
  <el-card header="语料生成与导出">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="模板管理" name="templates">
        <el-button type="primary" @click="openTemplateDialog()" style="margin-bottom:16px">新建模板</el-button>
        <el-table :data="templates" stripe v-loading="tplLoading">
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" @click="openTemplateDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDeleteTemplate(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="语料生成" name="generate">
        <el-form :model="genForm" label-width="100px">
          <el-form-item label="标签分组">
            <el-select v-model="genForm.group_id" placeholder="选择标签分组" @change="loadGroupLabels">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="模板">
            <el-select v-model="genForm.template_id" placeholder="选择模板">
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <el-select v-model="genForm.label_ids" multiple clearable placeholder="选择标签">
              <el-option v-for="l in genLabels" :key="l.id" :label="l.name" :value="l.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="预处理任务">
            <el-select v-model="genForm.task_id" clearable placeholder="选择预处理任务（可选）">
              <el-option v-for="t in tasks" :key="t.id" :label="t.name || `Task ${t.id}`" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="generating" @click="handleGenerate">生成语料</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="语料预览" name="records">
        <div style="display:flex;gap:12px;margin-bottom:16px;align-items:center">
          <el-select v-model="recFilter.group_id" placeholder="按标签分组筛选" clearable style="width:200px" @change="loadRecords">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <el-select v-model="recFilter.status" placeholder="按状态筛选" clearable style="width:150px" @change="loadRecords">
            <el-option label="草稿" value="draft" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已导出" value="exported" />
          </el-select>
          <el-button type="success" :disabled="selectedRecords.length === 0" @click="handleBatchConfirm">批量确认</el-button>
        </div>

        <el-table :data="records" stripe v-loading="recLoading" @selection-change="onRecordSelectionChange">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="image_id" label="图片ID" width="100" />
          <el-table-column label="缩略图" width="100">
            <template #default="{ row }">
              <el-image v-if="row.image_path" :src="recordImageUrl(row)" style="width:60px;height:60px" fit="cover" />
            </template>
          </el-table-column>
          <el-table-column label="输出文本" min-width="200">
            <template #default="{ row }">
              <el-popover trigger="hover" :width="400">
                <template #reference>
                  <span style="cursor:pointer">{{ truncate(row.output_text, 60) }}</span>
                </template>
                <div style="max-height:300px;overflow:auto;white-space:pre-wrap">{{ row.output_text }}</div>
              </el-popover>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button size="small" type="success" v-if="row.status === 'draft'" @click="handleConfirmOne(row.id)">确认</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="recPage"
          v-model:page-size="recPageSize"
          :total="recTotal"
          layout="total, prev, pager, next"
          style="margin-top:16px;justify-content:center"
          @current-change="loadRecords"
          @size-change="loadRecords"
        />
      </el-tab-pane>

      <el-tab-pane label="导出" name="export">
        <el-form :model="expForm" label-width="100px">
          <el-form-item label="输出目录">
            <el-input v-model="expForm.output_dir" placeholder="导出目录路径" />
          </el-form-item>
          <el-form-item label="标签分组">
            <el-select v-model="expForm.group_id" placeholder="选择标签分组">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="模板">
            <el-select v-model="expForm.template_id" placeholder="选择模板">
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态筛选">
            <el-select v-model="expForm.status_filter" placeholder="选择状态">
              <el-option label="已确认" value="confirmed" />
              <el-option label="全部" value="all" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="exporting" @click="handleExport">导出</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="tplDialogVisible" :title="tplEditing ? '编辑模板' : '新建模板'" width="500px">
    <el-form :model="tplForm" label-width="80px">
      <el-form-item label="名称">
        <el-input v-model="tplForm.name" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="tplForm.description" type="textarea" />
      </el-form-item>
      <el-form-item label="模板内容">
        <el-input v-model="tplForm.template_content" type="textarea" :rows="10" placeholder="Jinja2 模板代码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="tplDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="tplSaving" @click="handleSaveTemplate">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="editDialogVisible" title="编辑输出文本" width="500px">
    <el-input v-model="editForm.output_text" type="textarea" :rows="10" />
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSaveRecord">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listTemplates, createTemplate, updateTemplate, deleteTemplate, generateCorpus, listRecords, updateRecord, confirmRecords, exportCorpus } from '../api/corpus'
import { listGroups, listLabelsByGroup } from '../api/labels'
import { listTasks } from '../api/preprocess'

const activeTab = ref('templates')
const groups = ref([])
const templates = ref([])
const tasks = ref([])

const tplLoading = ref(false)
const tplDialogVisible = ref(false)
const tplEditing = ref(false)
const tplEditId = ref(null)
const tplSaving = ref(false)
const tplForm = ref({ name: '', description: '', template_content: '' })

const genForm = ref({ group_id: null, template_id: null, label_ids: [], task_id: null })
const genLabels = ref([])
const generating = ref(false)

const recFilter = ref({ group_id: null, status: null })
const records = ref([])
const recLoading = ref(false)
const recPage = ref(1)
const recPageSize = ref(20)
const recTotal = ref(0)
const selectedRecords = ref([])

const editDialogVisible = ref(false)
const editForm = ref({ id: null, output_text: '' })

const expForm = ref({ output_dir: '', group_id: null, template_id: null, status_filter: 'confirmed' })
const exporting = ref(false)

const truncate = (text, len) => {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

const statusTagType = (status) => {
  if (status === 'confirmed') return 'success'
  if (status === 'exported') return 'warning'
  return 'info'
}

const statusLabel = (status) => {
  if (status === 'confirmed') return '已确认'
  if (status === 'exported') return '已导出'
  return '草稿'
}

const recordImageUrl = (row) => {
  if (!row.image_path) return ''
  const parts = row.image_path.split('/')
  const filename = parts[parts.length - 1]
  return `/images/${filename}`
}

const loadGroups = async () => {
  const res = await listGroups()
  groups.value = res.data
}

const loadTemplates = async () => {
  tplLoading.value = true
  try {
    const res = await listTemplates()
    templates.value = res.data
  } finally {
    tplLoading.value = false
  }
}

const loadTasks = async () => {
  const res = await listTasks()
  tasks.value = res.data
}

const loadGroupLabels = async (groupId) => {
  if (!groupId) {
    genLabels.value = []
    genForm.value.label_ids = []
    return
  }
  const res = await listLabelsByGroup(groupId)
  genLabels.value = res.data
}

watch(() => genForm.value.group_id, (val) => {
  loadGroupLabels(val)
})

const openTemplateDialog = (row = null) => {
  if (row) {
    tplEditing.value = true
    tplEditId.value = row.id
    tplForm.value = { name: row.name, description: row.description, template_content: row.template_content }
  } else {
    tplEditing.value = false
    tplEditId.value = null
    tplForm.value = { name: '', description: '', template_content: '' }
  }
  tplDialogVisible.value = true
}

const handleSaveTemplate = async () => {
  tplSaving.value = true
  try {
    if (tplEditing.value) {
      await updateTemplate(tplEditId.value, tplForm.value)
      ElMessage.success('模板更新成功')
    } else {
      await createTemplate(tplForm.value)
      ElMessage.success('模板创建成功')
    }
    tplDialogVisible.value = false
    loadTemplates()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    tplSaving.value = false
  }
}

const handleDeleteTemplate = async (id) => {
  try {
    await deleteTemplate(id)
    ElMessage.success('模板删除成功')
    loadTemplates()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleGenerate = async () => {
  generating.value = true
  try {
    const res = await generateCorpus(genForm.value)
    const count = res.data.count || res.data.length || 0
    ElMessage.success(`语料生成成功，共 ${count} 条`)
    activeTab.value = 'records'
    loadRecords()
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

const loadRecords = async () => {
  recLoading.value = true
  try {
    const params = { page: recPage.value, page_size: recPageSize.value }
    if (recFilter.value.group_id) params.group_id = recFilter.value.group_id
    if (recFilter.value.status) params.status = recFilter.value.status
    const res = await listRecords(params)
    records.value = res.data.items || res.data
    recTotal.value = res.data.total || records.value.length
  } finally {
    recLoading.value = false
  }
}

const onRecordSelectionChange = (val) => {
  selectedRecords.value = val
}

const openEditDialog = (row) => {
  editForm.value = { id: row.id, output_text: row.output_text }
  editDialogVisible.value = true
}

const handleSaveRecord = async () => {
  try {
    await updateRecord(editForm.value.id, { output_text: editForm.value.output_text })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadRecords()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleConfirmOne = async (id) => {
  try {
    await confirmRecords({ record_ids: [id] })
    ElMessage.success('确认成功')
    loadRecords()
  } catch (e) {
    ElMessage.error('确认失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleBatchConfirm = async () => {
  try {
    await confirmRecords({ record_ids: selectedRecords.value.map(r => r.id) })
    ElMessage.success('批量确认成功')
    loadRecords()
  } catch (e) {
    ElMessage.error('批量确认失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const res = await exportCorpus(expForm.value)
    ElMessage.success('导出成功: ' + (res.data.file_path || res.data.output_dir || '完成'))
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadGroups()
  loadTemplates()
  loadTasks()
  loadRecords()
})
</script>