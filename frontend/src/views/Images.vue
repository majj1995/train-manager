<template>
  <el-row :gutter="20">
    <el-col :span="4">
      <el-card header="数据源目录" style="margin-bottom: 12px">
        <el-button type="primary" size="small" @click="showAddDir = true" style="margin-bottom: 8px; width: 100%">添加目录</el-button>
        <div v-for="d in directories" :key="d.id" style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
          <div>
            <span style="font-size: 13px">{{ d.path }}</span>
            <el-tag size="small" style="margin-left: 4px">{{ d.image_count }}张</el-tag>
          </div>
          <el-button size="small" type="danger" @click="doDeleteDir(d)">删除</el-button>
        </div>
      </el-card>

      <el-card>
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>标签分组</span>
            <el-button size="small" type="primary" @click="groupDialogVisible = true">新建分组</el-button>
          </div>
        </template>
        <el-tree
          :data="groupTree"
          node-key="id"
          highlight-current
          default-expand-all
          @node-click="onNodeClick"
        />
      </el-card>
    </el-col>

    <el-col :span="20">
      <el-card>
        <template #header>
          <div style="display:flex;gap:12px;align-items:center">
            <el-button type="primary" @click="importDialogVisible = true">导入图片</el-button>
            <el-button :disabled="selectedImages.length === 0" @click="batchAddDialogVisible = true">批量添加标签</el-button>
            <el-button :disabled="selectedImages.length === 0" @click="handleBatchRemove">批量移除标签</el-button>
            <el-select v-model="filterGroupId" placeholder="按标签分组筛选" clearable style="width:200px" @change="loadImages">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </div>
        </template>

        <el-table :data="images" @selection-change="onSelectionChange" v-loading="loading" stripe>
          <el-table-column type="selection" width="50" />
          <el-table-column label="缩略图" width="100">
            <template #default="{ row }">
              <el-image :src="imageUrl(row)" style="width:80px;height:80px" fit="cover" :preview-src-list="[imageUrl(row)]" :z-index="9999" />
            </template>
          </el-table-column>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="file_path" label="文件路径" min-width="200" />
          <el-table-column label="标签" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="tag in row.tags" :key="tag.id" closable size="small" @close="removeTag(row, tag)" style="margin-right:4px">{{ tag.name }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          style="margin-top:16px;justify-content:center"
          @current-change="loadImages"
          @size-change="loadImages"
        />
      </el-card>
    </el-col>
  </el-row>

  <el-dialog v-model="importDialogVisible" title="导入图片" width="400px">
    <el-form label-width="80px">
      <el-form-item label="目录路径">
        <el-input v-model="importDir" placeholder="本地目录路径" />
      </el-form-item>
      <el-form-item label="递归扫描">
        <el-switch v-model="importRecursive" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="importDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="groupDialogVisible" title="新建标签分组" width="400px">
    <el-form label-width="80px">
      <el-form-item label="名称">
        <el-input v-model="newGroupName" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="newGroupDesc" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="groupDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCreateGroup">创建</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="batchAddDialogVisible" title="批量添加标签" width="400px">
    <el-form label-width="80px">
      <el-form-item label="选择分组">
        <el-select v-model="batchAddGroupId" placeholder="选择标签分组" @change="loadBatchLabels">
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="选择标签">
        <el-select v-model="batchAddLabelIds" multiple placeholder="选择标签">
          <el-option v-for="l in batchLabels" :key="l.id" :label="l.name" :value="l.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="batchAddDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleBatchAdd">添加</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showAddDir" title="添加数据源目录" width="400px">
    <el-form>
      <el-form-item label="目录路径">
        <el-input v-model="newDirPath" placeholder="/path/to/images" />
      </el-form-item>
      <el-form-item label="递归扫描子目录">
        <el-switch v-model="newDirRecursive" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddDir = false">取消</el-button>
      <el-button type="primary" @click="doAddDir">添加</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { importImages, listImages } from '../api/images'
import { listGroups, createGroup, listLabelsByGroup, batchAddLabels, batchRemoveLabels } from '../api/labels'
import { addDirectory, listDirectories, deleteDirectory } from '../api/directories'

const groups = ref([])
const groupTree = ref([])
const images = ref([])
const selectedImages = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterGroupId = ref(null)
const currentGroupId = ref(null)

const importDialogVisible = ref(false)
const importDir = ref('')
const importRecursive = ref(true)
const importing = ref(false)

const groupDialogVisible = ref(false)
const newGroupName = ref('')
const newGroupDesc = ref('')

const batchAddDialogVisible = ref(false)
const batchAddGroupId = ref(null)
const batchAddLabelIds = ref([])
const batchLabels = ref([])

const directories = ref([])
const showAddDir = ref(false)
const newDirPath = ref('')
const newDirRecursive = ref(false)

const imageUrl = (row) => {
  const parts = row.file_path.split('/')
  const filename = parts[parts.length - 1]
  return `${import.meta.env.VITE_API_BASE_URL || ''}/images/${filename}`
}

const loadGroups = async () => {
  const res = await listGroups()
  groups.value = res.data
  buildTree()
}

const buildTree = async () => {
  const tree = []
  for (const g of groups.value) {
    const labelsRes = await listLabelsByGroup(g.id)
    const children = labelsRes.data.map(l => ({ id: `label-${l.id}`, label: l.name, isLabel: true, labelId: l.id, groupId: g.id }))
    tree.push({ id: `group-${g.id}`, label: g.name, children })
  }
  groupTree.value = tree
}

const onNodeClick = (node) => {
  if (node.isLabel) return
  const gId = node.id.replace('group-', '')
  currentGroupId.value = Number(gId)
  filterGroupId.value = Number(gId)
  loadImages()
}

const loadImages = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterGroupId.value) params.group_id = filterGroupId.value
    const res = await listImages(params)
    images.value = res.data.items || res.data
    total.value = res.data.total || images.value.length
  } finally {
    loading.value = false
  }
}

const onSelectionChange = (val) => {
  selectedImages.value = val
}

const handleImport = async () => {
  importing.value = true
  try {
    await importImages(importDir.value, importRecursive.value)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    importDir.value = ''
    loadImages()
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

const handleCreateGroup = async () => {
  await createGroup({ name: newGroupName.value, description: newGroupDesc.value })
  ElMessage.success('分组创建成功')
  groupDialogVisible.value = false
  newGroupName.value = ''
  newGroupDesc.value = ''
  loadGroups()
}

const loadBatchLabels = async () => {
  const res = await listLabelsByGroup(batchAddGroupId.value)
  batchLabels.value = res.data
}

const handleBatchAdd = async () => {
  await batchAddLabels({ image_ids: selectedImages.value.map(i => i.id), label_ids: batchAddLabelIds.value })
  ElMessage.success('标签添加成功')
  batchAddDialogVisible.value = false
  batchAddLabelIds.value = []
  loadImages()
}

const handleBatchRemove = async () => {
  if (batchAddGroupId.value === null && filterGroupId.value === null) {
    ElMessage.warning('请先选择一个标签分组')
    return
  }
  const groupId = batchAddGroupId.value || filterGroupId.value
  const labelsRes = await listLabelsByGroup(groupId)
  const labelIds = labelsRes.data.map(l => l.id)
  await batchRemoveLabels({ image_ids: selectedImages.value.map(i => i.id), label_ids: labelIds })
  ElMessage.success('标签移除成功')
  loadImages()
}

const removeTag = async (row, tag) => {
  await batchRemoveLabels({ image_ids: [row.id], label_ids: [tag.id] })
  ElMessage.success('标签移除成功')
  loadImages()
}

const loadDirectories = async () => {
  const res = await listDirectories()
  directories.value = res.data
}

const doAddDir = async () => {
  await addDirectory({ path: newDirPath.value, recursive: newDirRecursive.value })
  ElMessage.success('目录添加成功')
  showAddDir.value = false
  loadDirectories()
  loadImages()
}

const doDeleteDir = async (d) => {
  try {
    await ElMessageBox.confirm(`删除目录 ${d.path}？将删除仅属于该目录的图片。`, '确认删除')
  } catch { return }
  const res = await deleteDirectory(d.id)
  ElMessage.success(`删除 ${res.data.deleted_images_count} 张图片，保留 ${res.data.kept_images_count} 张图片`)
  loadDirectories()
  loadImages()
}

onMounted(() => {
  loadDirectories()
  loadGroups()
  loadImages()
})
</script>