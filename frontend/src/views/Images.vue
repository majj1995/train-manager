<template>
  <el-row :gutter="20">
    <el-col :span="4">
      <el-card header="数据源目录" style="margin-bottom: 12px">
        <el-button type="primary" size="small" @click="showAddDir = true" style="margin-bottom: 8px; width: 100%">添加目录</el-button>
        <div v-for="d in directories" :key="d.id" style="margin-bottom: 8px; cursor: pointer" @click="filterByDirectory(d)">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-size: 13px" :class="{ active: filterDirectoryId === d.id }">{{ d.path }}</span>
            <el-tag size="small" style="margin-left: 4px">{{ d.image_count }}张</el-tag>
          </div>
          <el-button size="small" type="danger" @click.stop="doDeleteDir(d)">删除</el-button>
        </div>
      </el-card>
    </el-col>

    <el-col :span="20">
      <el-card>
        <template #header>
          <div style="display:flex;gap:12px;align-items:center">
            <el-button :disabled="selectedImages.length === 0" @click="batchAddDialogVisible = true">批量添加标签</el-button>
            <el-button :disabled="selectedImages.length === 0" @click="handleBatchRemove">批量移除标签</el-button>
            <el-button :disabled="selectedImages.length === 0" type="danger" @click="handleDeleteSelected">删除选中图片</el-button>
            <el-button type="danger" @click="deleteByPathDialogVisible = true">按路径删除</el-button>
            <el-select v-model="filterGroupId" placeholder="按标签分组筛选" clearable style="width:200px" @change="loadImages">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </div>
        </template>

        <el-table :data="images" @selection-change="onSelectionChange" v-loading="loading" stripe>
          <el-table-column type="selection" width="50" />
          <el-table-column label="缩略图" width="100">
            <template #default="{ row }">
              <el-image :src="imageUrl(row)" style="width:80px;height:80px;cursor:pointer" fit="cover" @click="previewImage(row)" />
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

  <el-dialog v-model="deleteByPathDialogVisible" title="按路径删除图片" width="400px">
    <el-form label-width="80px">
      <el-form-item label="路径前缀">
        <el-input v-model="deletePathPrefix" placeholder="/path/to/images" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="deleteByPathDialogVisible = false">取消</el-button>
      <el-button type="danger" @click="handleDeleteByPath">删除</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="previewVisible" width="auto" :show-close="true" align-center class="preview-dialog" @close="previewVisible = false">
    <img :src="previewImageUrl" style="max-width:90vw;max-height:80vh;display:block" />
  </el-dialog>

  <el-dialog v-model="batchAddDialogVisible" title="批量添加标签" width="400px">
    <el-form label-width="80px">
      <el-form-item label="选择分组">
        <el-select v-model="batchAddGroupId" placeholder="选择标签分组" @change="loadBatchLabels">
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="选择标签">
        <el-tree-select
          v-model="batchAddLabelIds"
          :data="batchLabelTree"
          multiple
          check-strictly
          :render-after-expand="false"
          placeholder="选择标签"
          style="width: 100%"
        />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listImages, deleteImagesByIds, deleteImagesByPath } from '../api/images'
import { listGroups, getLabelTree, batchAddLabels, batchRemoveLabels } from '../api/labels'
import { addDirectory, listDirectories, deleteDirectory } from '../api/directories'

const groups = ref([])
const images = ref([])
const selectedImages = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterGroupId = ref(null)
const filterDirectoryId = ref(null)

const batchAddDialogVisible = ref(false)
const batchAddGroupId = ref(null)
const batchAddLabelIds = ref([])
const batchLabelTree = ref([])

const directories = ref([])
const showAddDir = ref(false)
const newDirPath = ref('')
const newDirRecursive = ref(false)

const deleteByPathDialogVisible = ref(false)
const deletePathPrefix = ref('')

const previewVisible = ref(false)
const previewImageUrl = ref('')

const imageUrl = (row) => {
  const parts = row.file_path.split('/')
  const filename = parts[parts.length - 1]
  return `${import.meta.env.VITE_API_BASE_URL || ''}/images/${filename}`
}

const previewImage = (row) => {
  previewImageUrl.value = imageUrl(row)
  previewVisible.value = true
}

const loadGroups = async () => {
  const res = await listGroups()
  groups.value = res.data
}

const loadBatchLabels = async () => {
  if (!batchAddGroupId.value) return
  const res = await getLabelTree(batchAddGroupId.value)
  batchLabelTree.value = res.data
}

const loadImages = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterGroupId.value) params.group_id = filterGroupId.value
    if (filterDirectoryId.value) params.directory_id = filterDirectoryId.value
    const res = await listImages(params)
    images.value = res.data.items || res.data
    total.value = res.data.total || images.value.length
  } finally {
    loading.value = false
  }
}

const filterByDirectory = (d) => {
  filterDirectoryId.value = d.id
  filterGroupId.value = null
  loadImages()
}

const onSelectionChange = (val) => {
  selectedImages.value = val
}

const handleBatchAdd = async () => {
  await batchAddLabels({ image_ids: selectedImages.value.map(i => i.id), label_ids: batchAddLabelIds.value })
  ElMessage.success('标签添加成功')
  batchAddDialogVisible.value = false
  batchAddLabelIds.value = []
  loadImages()
}

const handleBatchRemove = async () => {
  if (filterGroupId.value === null) {
    ElMessage.warning('请先选择一个标签分组筛选条件')
    return
  }
  const treeRes = await getLabelTree(filterGroupId.value)
  const allLabelIds = collectAllLabelIds(treeRes.data)
  await batchRemoveLabels({ image_ids: selectedImages.value.map(i => i.id), label_ids: allLabelIds })
  ElMessage.success('标签移除成功')
  loadImages()
}

const collectAllLabelIds = (tree) => {
  const ids = []
  for (const node of tree) {
    ids.push(node.id)
    if (node.children) ids.push(...collectAllLabelIds(node.children))
  }
  return ids
}

const removeTag = async (row, tag) => {
  await batchRemoveLabels({ image_ids: [row.id], label_ids: [tag.id] })
  ElMessage.success('标签移除成功')
  loadImages()
}

const handleDeleteSelected = async () => {
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedImages.value.length} 张图片？`, '确认删除')
  } catch { return }
  await deleteImagesByIds(selectedImages.value.map(i => i.id))
  ElMessage.success('删除成功')
  loadDirectories()
  loadImages()
}

const handleDeleteByPath = async () => {
  if (!deletePathPrefix.value) {
    ElMessage.warning('请输入路径前缀')
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除路径以 "${deletePathPrefix.value}" 开头的所有图片？`, '确认删除')
  } catch { return }
  const res = await deleteImagesByPath(deletePathPrefix.value)
  ElMessage.success(`已删除 ${res.data.deleted_count} 张图片`)
  deleteByPathDialogVisible.value = false
  deletePathPrefix.value = ''
  loadDirectories()
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
