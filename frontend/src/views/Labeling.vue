<template>
  <el-card>
    <el-row style="margin-bottom: 12px">
      <el-select v-model="groupId" placeholder="选择标签分组" @change="loadData" style="width: 200px">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>
      <el-select v-model="labelFilterId" placeholder="按标签过滤" clearable @change="loadImages" style="width: 200px; margin-left: 12px">
        <el-option v-for="l in groupLabels" :key="l.id" :label="l.name" :value="l.id" />
      </el-select>
      <el-tag style="margin-left: 12px">共 {{ filteredImages.length }} 张图片</el-tag>
    </el-row>
    <ImageGrid :images="filteredImages" @select="onSelectImage" />
    <LabelPanel :image="selectedImage" :groupLabels="groupLabels" :groupId="groupId" @saved="loadImages" />
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ImageGrid from '../components/ImageGrid.vue'
import LabelPanel from '../components/LabelPanel.vue'
import { listGroups, listLabelsByGroup } from '../api/labels'
import { listImages } from '../api/images'

const groups = ref([])
const groupId = ref(null)
const groupLabels = ref([])
const allImages = ref([])
const labelFilterId = ref(null)
const selectedImage = ref(null)

const filteredImages = computed(() => {
  if (!labelFilterId.value) return allImages.value
  return allImages.value.filter(img => img.labels && img.labels.some(l => l.id === labelFilterId.value))
})

const loadData = async () => {
  if (!groupId.value) return
  await loadGroupLabels()
  await loadImages()
}

const loadGroupLabels = async () => {
  if (!groupId.value) return
  const res = await listLabelsByGroup(groupId.value)
  groupLabels.value = res.data
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