<template>
  <el-card>
    <el-row style="margin-bottom: 12px">
      <el-select v-model="groupId" placeholder="选择标签分组" @change="loadData" style="width: 200px">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>
      <el-tree-select
        v-model="labelFilterId"
        :data="labelTree"
        :props="{ value: 'id', label: 'name', children: 'children' }"
        check-strictly
        :render-after-expand="false"
        clearable
        placeholder="按标签过滤"
        style="width: 200px; margin-left: 12px"
        @change="onLabelFilterChange"
      />
      <el-tag style="margin-left: 12px">共 {{ filteredImages.length }} 张图片</el-tag>
      <el-button @click="batchAddDialogVisible = true" style="margin-left: 12px">批量添加标签</el-button>
      <el-button @click="batchRemoveDialogVisible = true" style="margin-left: 4px">批量移除标签</el-button>
    </el-row>
    <ImageGrid :images="filteredImages" @select="onSelectImage" />
    <LabelPanel :image="selectedImage" :labelTree="labelTree" :groupId="groupId" @saved="loadImages" />
  </el-card>

  <el-dialog v-model="batchAddDialogVisible" title="批量添加标签" width="400px">
    <p style="margin-bottom:12px;color:#666">将对当前筛选范围内的所有图片（共 {{ filteredImages.length }} 张）添加标签</p>
    <el-form label-width="80px">
      <el-form-item label="选择标签">
        <el-tree-select
          v-model="batchAddLabelIds"
          :data="labelTree"
          :props="{ value: 'id', label: 'name', children: 'children' }"
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

  <el-dialog v-model="batchRemoveDialogVisible" title="批量移除标签" width="400px">
    <p style="margin-bottom:12px;color:#666">将从当前筛选范围内的所有图片（共 {{ filteredImages.length }} 张）移除标签</p>
    <el-form label-width="80px">
      <el-form-item label="选择标签">
        <el-tree-select
          v-model="batchRemoveLabelIds"
          :data="labelTree"
          :props="{ value: 'id', label: 'name', children: 'children' }"
          multiple
          check-strictly
          :render-after-expand="false"
          placeholder="选择要移除的标签"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="batchRemoveDialogVisible = false">取消</el-button>
      <el-button type="danger" @click="handleBatchRemove">移除</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ImageGrid from '../components/ImageGrid.vue'
import LabelPanel from '../components/LabelPanel.vue'
import { listGroups, getLabelTree, batchAddLabels, batchRemoveLabels } from '../api/labels'
import { listImages } from '../api/images'

const groups = ref([])
const groupId = ref(null)
const labelTree = ref([])
const allImages = ref([])
const labelFilterId = ref(null)
const selectedImage = ref(null)
const batchAddDialogVisible = ref(false)
const batchAddLabelIds = ref([])
const batchRemoveDialogVisible = ref(false)
const batchRemoveLabelIds = ref([])

const filteredImages = computed(() => {
  if (!labelFilterId.value) return allImages.value
  return allImages.value.filter(img => img.tags && img.tags.some(l => l.id === labelFilterId.value))
})

const loadData = async () => {
  if (!groupId.value) return
  await loadLabelTree()
  await loadImages()
}

const loadLabelTree = async () => {
  if (!groupId.value) return
  const res = await getLabelTree(groupId.value)
  labelTree.value = res.data
}

const loadImages = async () => {
  const params = { page_size: 500 }
  if (groupId.value) params.group_id = groupId.value
  if (labelFilterId.value) params.label_id = labelFilterId.value
  const res = await listImages(params)
  allImages.value = res.data.items
}

const onLabelFilterChange = () => {
  loadImages()
}

const onSelectImage = (img) => { selectedImage.value = img }

const handleBatchAdd = async () => {
  await batchAddLabels({ image_ids: filteredImages.value.map(i => i.id), label_ids: batchAddLabelIds.value })
  ElMessage.success('标签添加成功')
  batchAddDialogVisible.value = false
  batchAddLabelIds.value = []
  loadImages()
}

const handleBatchRemove = async () => {
  await batchRemoveLabels({ image_ids: filteredImages.value.map(i => i.id), label_ids: batchRemoveLabelIds.value })
  ElMessage.success('标签移除成功')
  batchRemoveDialogVisible.value = false
  batchRemoveLabelIds.value = []
  loadImages()
}

onMounted(async () => {
  const res = await listGroups()
  groups.value = res.data
  if (groups.value.length) {
    groupId.value = groups.value[0].id
    loadData()
  }
})
</script>
