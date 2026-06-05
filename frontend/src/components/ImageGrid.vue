<template>
  <div class="image-grid" ref="gridContainer" @scroll="onScroll">
    <div class="grid-inner" :style="{ height: totalHeight + 'px' }">
      <div v-for="item in visibleItems" :key="item.id" class="grid-item" :style="{ transform: `translateY(${item.top}px)` }" @click="$emit('select', item)">
        <el-image :src="imageUrl(item.file_path)" fit="cover" lazy style="width: 100%; height: 150px" />
        <div class="tags-row">
          <el-tag v-for="l in item.labels" :key="l.id" :color="l.color" size="small">{{ l.name }}</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  images: Array,
  itemHeight: { type: Number, default: 180 },
  columns: { type: Number, default: 5 },
  gap: { type: Number, default: 10 },
})
const emit = defineEmits(['select'])

const gridContainer = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(800)

const imageUrl = (filePath) => `${import.meta.env.VITE_API_BASE_URL || ''}/images/${filePath.split('/').pop()}`

const rowHeight = computed(() => props.itemHeight + props.gap)
const totalRows = computed(() => Math.ceil(props.images.length / props.columns))
const totalHeight = computed(() => totalRows.value * rowHeight.value)

const startRow = computed(() => Math.floor(scrollTop.value / rowHeight.value))
const visibleRows = computed(() => Math.ceil(containerHeight.value / rowHeight.value) + 2)
const endRow = computed(() => Math.min(totalRows.value, startRow.value + visibleRows.value))

const visibleItems = computed(() => {
  const items = []
  for (let row = startRow.value; row < endRow.value; row++) {
    for (let col = 0; col < props.columns; col++) {
      const idx = row * props.columns + col
      if (idx < props.images.length) {
        items.push({ ...props.images[idx], top: row * rowHeight.value })
      }
    }
  }
  return items
})

const onScroll = () => {
  if (gridContainer.value) scrollTop.value = gridContainer.value.scrollTop
}

onMounted(() => {
  if (gridContainer.value) containerHeight.value = gridContainer.value.clientHeight
})
</script>

<style scoped>
.image-grid { height: 100%; overflow-y: auto; position: relative; }
.grid-inner { position: relative; }
.grid-item { position: absolute; width: calc(20% - 10px); margin: 5px; cursor: pointer; }
.tags-row { display: flex; flex-wrap: wrap; gap: 2px; padding: 4px; }
</style>