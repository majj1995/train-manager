<template>
  <el-dialog v-model="visible" :title="`标注 - ${image?.file_path?.split('/').pop() || ''}`" width="600px">
    <div style="text-align: center; margin-bottom: 16px">
      <el-image :src="imageUrl" fit="contain" style="max-height: 300px" />
    </div>
    <el-divider>标签标注</el-divider>
    <el-checkbox-group v-model="selectedLabelIds">
      <el-checkbox v-for="label in groupLabels" :key="label.id" :label="label.id">
        <el-tag :color="label.color" size="small">{{ label.name }}</el-tag>
      </el-checkbox>
    </el-checkbox-group>
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
  groupLabels: Array,
  groupId: Number,
})
const emit = defineEmits(['saved'])

const visible = ref(false)
const selectedLabelIds = ref([])
const imageUrl = computed(() => props.image ? `/images/${props.image.file_path.split('/').pop()}` : '')

watch(() => props.image, (img) => {
  if (img) {
    selectedLabelIds.value = img.labels
      .filter(l => l.group_id === props.groupId)
      .map(l => l.id)
    visible.value = true
  }
})

const saveLabels = async () => {
  const existingIds = props.image.labels.filter(l => l.group_id === props.groupId).map(l => l.id)
  const toAdd = selectedLabelIds.value.filter(id => !existingIds.includes(id))
  const toRemove = existingIds.filter(id => !selectedLabelIds.value.includes(id))

  if (toAdd.length) await batchAddLabels({ image_ids: [props.image.id], label_ids: toAdd })
  if (toRemove.length) await batchRemoveLabels({ image_ids: [props.image.id], label_ids: toRemove })

  ElMessage.success('标注已保存')
  visible.value = false
  emit('saved')
}
</script>