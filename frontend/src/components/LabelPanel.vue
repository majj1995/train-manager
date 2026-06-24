<template>
  <el-dialog v-model="visible" :title="`标注 - ${image?.file_path?.split('/').pop() || ''}`" width="600px">
    <div style="text-align: center; margin-bottom: 16px">
      <el-image :src="imageUrl" fit="contain" style="max-height: 300px" />
    </div>
    <el-divider>标签标注</el-divider>
    <el-tree
      :data="labelTree"
      node-key="id"
      show-checkbox
      check-strictly
      :default-checked-keys="selectedLabelIds"
      :props="{ children: 'children', label: 'name' }"
      @check="onCheck"
    >
      <template #default="{ node, data }">
        <span style="display:flex;align-items:center">
          <span :style="{ color: data.color || '#409EFF' }">{{ data.name }}</span>
        </span>
      </template>
    </el-tree>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="saveLabels">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { batchAddLabels, batchRemoveLabels } from '../api/labels'

const props = defineProps({
  image: Object,
  labelTree: Array,
  groupId: Number,
})
const emit = defineEmits(['saved'])

const visible = ref(false)
const selectedLabelIds = ref([])
const checkedLabelIds = ref([])
const imageUrl = computed(() => props.image ? `${import.meta.env.VITE_API_BASE_URL || ''}/images/${props.image.file_path.split('/').pop()}` : '')

watch(() => props.image, (img) => {
  if (img) {
    selectedLabelIds.value = img.labels
      .filter(l => l.group_id === props.groupId)
      .map(l => l.id)
    checkedLabelIds.value = [...selectedLabelIds.value]
    visible.value = true
  }
})

const onCheck = (data, checkedInfo) => {
  checkedLabelIds.value = checkedInfo.checkedKeys
}

const collectAllIds = (tree) => {
  const ids = []
  for (const node of tree) {
    ids.push(node.id)
    if (node.children) ids.push(...collectAllIds(node.children))
  }
  return ids
}

const saveLabels = async () => {
  const toAdd = checkedLabelIds.value.filter(id => !selectedLabelIds.value.includes(id))
  const toRemove = selectedLabelIds.value.filter(id => !checkedLabelIds.value.includes(id))

  if (toAdd.length) await batchAddLabels({ image_ids: [props.image.id], label_ids: toAdd })
  if (toRemove.length) await batchRemoveLabels({ image_ids: [props.image.id], label_ids: toRemove })

  ElMessage.success('标注已保存')
  visible.value = false
  emit('saved')
}
</script>
