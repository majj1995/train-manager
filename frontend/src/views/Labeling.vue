<template>
  <el-card>
    <el-row style="margin-bottom: 12px">
      <el-select v-model="groupId" placeholder="选择标签分组" @change="loadData" style="width: 200px">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>
      <el-tree-select
        v-model="labelFilterId"
        :data="labelTree"
        check-strictly
        :render-after-expand="false"
        clearable
        placeholder="按标签过滤"
        style="width: 200px; margin-left: 12px"
        @change="loadImages"
      />
      <el-tag style="margin-left: 12px">共 {{ filteredImages.length }} 张图片</el-tag>
    </el-row>
    <ImageGrid :images="filteredImages" @select="onSelectImage" />
    <LabelPanel :image="selectedImage" :labelTree="labelTree" :groupId="groupId" @saved="loadImages" />
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ImageGrid from '../components/ImageGrid.vue'
import LabelPanel from '../components/LabelPanel.vue'
import { listGroups, getLabelTree } from '../api/labels'
import { listImages } from '../api/images'

const groups = ref([])
const groupId = ref(null)
const labelTree = ref([])
const allImages = ref([])
const labelFilterId = ref(null)
const selectedImage = ref(null)

const filteredImages = computed(() => {
  if (!labelFilterId.value) return allImages.value
  return allImages.value.filter(img => img.labels && img.labels.some(l => l.id === labelFilterId.value))
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
  const params = { page_size: 500, group_id: groupId.value }
  if (labelFilterId.value) params.label_id = labelFilterId.value
  const res = await listImages(params)
  allImages.value = res.data.items
}

const onSelectImage = (img) => { selectedImage.value = img }

onMounted(async () => {
  const res = await listGroups()
  groups.value = res.data
  if (groups.value.length) {
    groupId.value = groups.value[0].id
    loadData()
  }
})
</script>
