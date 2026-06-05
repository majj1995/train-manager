<template>
  <el-card header="预处理">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="脚本管理" name="scripts">
        <el-button type="primary" @click="openScriptDialog" style="margin-bottom: 16px">新建脚本</el-button>
        <el-table :data="scripts" border stripe>
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型">
            <template #default="{ row }">
              {{ row.type === 'local_python' ? '本地Python' : '模型API' }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleDeleteScript(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-dialog v-model="scriptDialogVisible" title="新建脚本" width="600px">
          <el-form :model="scriptForm" label-width="100px">
            <el-form-item label="名称">
              <el-input v-model="scriptForm.name" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="scriptForm.type" style="width: 100%">
                <el-option label="本地Python" value="local_python" />
                <el-option label="模型API" value="model_api" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="scriptForm.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item v-if="scriptForm.type === 'local_python'" label="代码">
              <el-input v-model="scriptForm.code" type="textarea" :rows="8" />
            </el-form-item>
            <el-form-item v-if="scriptForm.type === 'model_api'" label="API配置">
              <el-input v-model="scriptForm.api_config" type="textarea" :rows="8" placeholder="JSON格式" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="scriptDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleCreateScript">确定</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="任务管理" name="tasks">
        <el-button type="primary" @click="openTaskDialog" style="margin-bottom: 16px">新建任务</el-button>
        <el-table :data="tasks" border stripe>
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="script_name" label="脚本" />
          <el-table-column label="父任务" width="120">
            <template #default="{ row }">
              {{ row.parent_task_id || '无' }}
            </template>
          </el-table-column>
          <el-table-column label="标注输出" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_label_output ? 'success' : 'info'" size="small">
                {{ row.is_label_output ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusColor(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="viewResults(row)">查看结果</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-dialog v-model="taskDialogVisible" title="新建任务" width="600px">
          <el-form :model="taskForm" label-width="100px">
            <el-form-item label="名称">
              <el-input v-model="taskForm.name" />
            </el-form-item>
            <el-form-item label="脚本">
              <el-select v-model="taskForm.script_id" style="width: 100%">
                <el-option v-for="s in scripts" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="父任务">
              <el-select v-model="taskForm.parent_task_id" clearable style="width: 100%" placeholder="无">
                <el-option v-for="t in tasks" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="标注输出">
              <el-switch v-model="taskForm.is_label_output" />
            </el-form-item>
            <el-form-item label="范围类型">
              <el-select v-model="taskForm.scope_type" style="width: 100%">
                <el-option label="全部" value="all" />
                <el-option label="按标签" value="by_labels" />
                <el-option label="手动" value="manual" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="taskForm.scope_type === 'by_labels'" label="标签">
              <el-select v-model="taskForm.label_ids" multiple style="width: 100%">
                <el-option v-for="l in availableLabels" :key="l.id" :label="l.name" :value="l.id" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="taskDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleCreateTask">确定</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane v-if="currentTaskId" label="结果浏览" name="results">
        <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
          <span>任务: {{ currentTask?.name }}</span>
          <el-button v-if="currentTask?.is_label_output" type="success" @click="handleBatchConfirm">批量确认</el-button>
        </div>
        <el-table :data="results" border stripe>
          <el-table-column label="图片" width="100">
            <template #default="{ row }">
              <el-image :src="row.image_url" style="width: 60px; height: 60px" fit="cover" />
            </template>
          </el-table-column>
          <el-table-column prop="image_id" label="图片ID" width="120" />
          <el-table-column label="结果" min-width="200">
            <template #default="{ row }">
              <el-popover trigger="hover" width="400">
                <template #reference>
                  <span>{{ truncateResult(row.result) }}</span>
                </template>
                <pre style="max-height: 300px; overflow: auto; white-space: pre-wrap">{{ formatJSON(row.result) }}</pre>
              </el-popover>
            </template>
          </el-table-column>
          <el-table-column label="手动修改" width="100">
            <template #default="{ row }">
              <el-tag :type="row.manually_modified ? 'warning' : 'info'" size="small">
                {{ row.manually_modified ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="已确认" width="100">
            <template #default="{ row }">
              <el-tag :type="row.confirmed ? 'success' : 'info'" size="small">
                {{ row.confirmed ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button v-if="currentTask?.is_label_output && !row.confirmed" type="success" size="small" @click="handleConfirmResult(row)">确认</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="resultPagination.page"
          v-model:page-size="resultPagination.pageSize"
          :total="resultPagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          style="margin-top: 16px; justify-content: center"
          @current-change="loadResults"
          @size-change="loadResults"
        />

        <el-dialog v-model="editDialogVisible" title="编辑结果" width="600px">
          <el-input v-model="editForm.result" type="textarea" :rows="10" />
          <template #footer>
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleUpdateResult">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listScripts, createScript, deleteScript, listTasks, createTask, getTask, getTaskResults, updateResult, confirmResults } from '../api/preprocess'
import { listLabelsByGroup } from '../api/labels'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('scripts')
const scripts = ref([])
const tasks = ref([])
const currentTaskId = ref(null)
const currentTask = ref(null)
const results = ref([])

const scriptDialogVisible = ref(false)
const taskDialogVisible = ref(false)
const editDialogVisible = ref(false)

const scriptForm = reactive({ name: '', type: 'local_python', description: '', code: '', api_config: '' })
const taskForm = reactive({ name: '', script_id: null, parent_task_id: null, is_label_output: false, scope_type: 'all', label_ids: [] })
const editForm = reactive({ id: null, result: '' })

const resultPagination = reactive({ page: 1, pageSize: 10, total: 0 })
const availableLabels = ref([])

const statusColor = (status) => {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}
const statusText = (status) => {
  const map = { pending: '等待', running: '运行中', completed: '完成', failed: '失败' }
  return map[status] || status
}

const truncateResult = (result) => {
  if (!result) return ''
  const str = typeof result === 'object' ? JSON.stringify(result) : String(result)
  return str.length > 50 ? str.substring(0, 50) + '...' : str
}
const formatJSON = (result) => {
  if (!result) return ''
  try {
    return JSON.stringify(typeof result === 'object' ? result : JSON.parse(result), null, 2)
  } catch {
    return String(result)
  }
}

const loadScripts = async () => {
  try {
    const { data } = await listScripts()
    scripts.value = data
  } catch (e) {
    ElMessage.error('加载脚本失败')
  }
}

const loadTasks = async () => {
  try {
    const { data } = await listTasks()
    tasks.value = data
  } catch (e) {
    ElMessage.error('加载任务失败')
  }
}

const loadResults = async () => {
  if (!currentTaskId.value) return
  try {
    const { data } = await getTaskResults(currentTaskId.value, { page: resultPagination.page, page_size: resultPagination.pageSize })
    results.value = data.items || data
    resultPagination.total = data.total || results.value.length
  } catch (e) {
    ElMessage.error('加载结果失败')
  }
}

const openScriptDialog = () => {
  scriptForm.name = ''
  scriptForm.type = 'local_python'
  scriptForm.description = ''
  scriptForm.code = ''
  scriptForm.api_config = ''
  scriptDialogVisible.value = true
}

const handleCreateScript = async () => {
  try {
    const payload = { name: scriptForm.name, type: scriptForm.type, description: scriptForm.description }
    if (scriptForm.type === 'local_python') {
      payload.code = scriptForm.code
    } else {
      payload.api_config = scriptForm.api_config
    }
    await createScript(payload)
    scriptDialogVisible.value = false
    ElMessage.success('脚本创建成功')
    loadScripts()
  } catch (e) {
    ElMessage.error('创建脚本失败')
  }
}

const handleDeleteScript = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该脚本?', '提示', { type: 'warning' })
    await deleteScript(id)
    ElMessage.success('脚本已删除')
    loadScripts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除脚本失败')
  }
}

const openTaskDialog = () => {
  taskForm.name = ''
  taskForm.script_id = null
  taskForm.parent_task_id = null
  taskForm.is_label_output = false
  taskForm.scope_type = 'all'
  taskForm.label_ids = []
  taskDialogVisible.value = true
}

const handleCreateTask = async () => {
  try {
    const payload = {
      name: taskForm.name,
      script_id: taskForm.script_id,
      parent_task_id: taskForm.parent_task_id || null,
      is_label_output: taskForm.is_label_output,
      scope_type: taskForm.scope_type,
      label_ids: taskForm.scope_type === 'by_labels' ? taskForm.label_ids : [],
    }
    await createTask(payload)
    taskDialogVisible.value = false
    ElMessage.success('任务创建成功')
    loadTasks()
  } catch (e) {
    ElMessage.error('创建任务失败')
  }
}

const viewResults = async (row) => {
  currentTaskId.value = row.id
  try {
    const { data } = await getTask(row.id)
    currentTask.value = data
  } catch (e) {
    ElMessage.error('加载任务详情失败')
    return
  }
  resultPagination.page = 1
  activeTab.value = 'results'
  loadResults()
}

const openEditDialog = (row) => {
  editForm.id = row.id
  editForm.result = typeof row.result === 'object' ? JSON.stringify(row.result, null, 2) : String(row.result || '')
  editDialogVisible.value = true
}

const handleUpdateResult = async () => {
  try {
    let resultValue
    try {
      resultValue = JSON.parse(editForm.result)
    } catch {
      resultValue = editForm.result
    }
    await updateResult(editForm.id, { result: resultValue })
    editDialogVisible.value = false
    ElMessage.success('结果更新成功')
    loadResults()
  } catch (e) {
    ElMessage.error('更新结果失败')
  }
}

const handleConfirmResult = async (row) => {
  try {
    await confirmResults({ task_id: currentTaskId.value, result_ids: [row.id] })
    ElMessage.success('确认成功')
    loadResults()
  } catch (e) {
    ElMessage.error('确认失败')
  }
}

const handleBatchConfirm = async () => {
  const unconfirmed = results.value.filter(r => !r.confirmed)
  if (unconfirmed.length === 0) {
    ElMessage.info('没有未确认的结果')
    return
  }
  try {
    await confirmResults({ task_id: currentTaskId.value, result_ids: unconfirmed.map(r => r.id) })
    ElMessage.success('批量确认成功')
    loadResults()
  } catch (e) {
    ElMessage.error('批量确认失败')
  }
}

const loadLabels = async () => {
  try {
    const { data } = await listLabelsByGroup(1)
    availableLabels.value = Array.isArray(data) ? data : []
  } catch {
    availableLabels.value = []
  }
}

onMounted(() => {
  loadScripts()
  loadTasks()
  loadLabels()
})
</script>