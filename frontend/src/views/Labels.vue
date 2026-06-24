<template>
  <el-row :gutter="20">
    <el-col :span="6">
      <el-card>
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>标签分组</span>
            <el-button size="small" type="primary" @click="groupDialogVisible = true">新建分组</el-button>
          </div>
        </template>
        <div v-for="g in groups" :key="g.id" style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;padding:6px 8px;border-radius:4px" :style="{ background: selectedGroupId === g.id ? '#ecf5ff' : '' }" @click="selectGroup(g)">
          <span style="font-size:14px">{{ g.name }}</span>
          <el-button size="small" type="danger" text @click.stop="handleDeleteGroup(g)">删除</el-button>
        </div>
      </el-card>
    </el-col>

    <el-col :span="18">
      <el-card v-if="selectedGroupId">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>{{ selectedGroup?.name }} - 标签树</span>
            <div>
              <el-button size="small" type="primary" @click="openAddTopLabel">添加顶层标签</el-button>
              <el-button size="small" type="primary" :disabled="!currentNode" @click="openAddChildLabel">添加子标签</el-button>
              <el-button size="small" :disabled="!currentNode" @click="openEditLabel">编辑</el-button>
              <el-button size="small" type="danger" :disabled="!currentNode" @click="handleDeleteLabel">删除</el-button>
            </div>
          </div>
        </template>

        <el-tree
          :data="treeData"
          node-key="id"
          highlight-current
          default-expand-all
          :props="{ children: 'children', label: 'name' }"
          @node-click="onNodeClick"
        >
          <template #default="{ node, data }">
            <span style="display:flex;align-items:center">
              <span :style="{ color: data.color || '#409EFF', fontWeight: 'bold' }">{{ data.name }}</span>
              <span v-if="data.description" style="margin-left:8px;font-size:12px;color:#999">{{ data.description }}</span>
            </span>
          </template>
        </el-tree>
      </el-card>

      <el-card v-else>
        <el-empty description="请从左侧选择一个标签分组" />
      </el-card>
    </el-col>
  </el-row>

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

  <el-dialog v-model="labelDialogVisible" :title="labelDialogTitle" width="400px">
    <el-form label-width="80px">
      <el-form-item label="名称">
        <el-input v-model="labelForm.name" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="labelForm.description" type="textarea" />
      </el-form-item>
      <el-form-item label="颜色">
        <el-color-picker v-model="labelForm.color" />
      </el-form-item>
      <el-form-item v-if="labelDialogMode === 'addChild'" label="父标签">
        <span>{{ currentNode?.name }}</span>
      </el-form-item>
      <el-form-item v-if="labelDialogMode === 'edit'" label="父标签">
        <el-select v-model="labelForm.parent_id" clearable placeholder="无（顶层标签）">
          <el-option v-for="l in flatLabels" :key="l.id" :label="l.name" :value="l.id" :disabled="l.id === currentNode?.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="labelDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSaveLabel">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listGroups, createGroup, deleteGroup, getLabelTree, createLabel, updateLabel, deleteLabel, listLabelsByGroup } from '../api/labels'

const groups = ref([])
const selectedGroupId = ref(null)
const selectedGroup = ref(null)
const treeData = ref([])
const flatLabels = ref([])
const currentNode = ref(null)

const groupDialogVisible = ref(false)
const newGroupName = ref('')
const newGroupDesc = ref('')

const labelDialogVisible = ref(false)
const labelDialogMode = ref('addTop')
const labelDialogTitle = ref('')
const labelForm = ref({ name: '', description: '', color: '#409EFF', parent_id: null })

const loadGroups = async () => {
  const res = await listGroups()
  groups.value = res.data
  if (selectedGroupId.value) {
    selectedGroup.value = groups.value.find(g => g.id === selectedGroupId.value)
  }
}

const selectGroup = (g) => {
  selectedGroupId.value = g.id
  selectedGroup.value = g
  currentNode.value = null
  loadTree()
}

const loadTree = async () => {
  if (!selectedGroupId.value) return
  const res = await getLabelTree(selectedGroupId.value)
  treeData.value = res.data
  const flatRes = await listLabelsByGroup(selectedGroupId.value)
  flatLabels.value = flatRes.data
}

const onNodeClick = (data) => {
  currentNode.value = data
}

const handleCreateGroup = async () => {
  await createGroup({ name: newGroupName.value, description: newGroupDesc.value })
  ElMessage.success('分组创建成功')
  groupDialogVisible.value = false
  newGroupName.value = ''
  newGroupDesc.value = ''
  loadGroups()
}

const handleDeleteGroup = async (g) => {
  try {
    await ElMessageBox.confirm(`删除分组 "${g.name}" 及其下所有标签？`, '确认删除')
  } catch { return }
  await deleteGroup(g.id)
  ElMessage.success('分组删除成功')
  if (selectedGroupId.value === g.id) {
    selectedGroupId.value = null
    selectedGroup.value = null
    treeData.value = []
  }
  loadGroups()
}

const openAddTopLabel = () => {
  labelDialogMode.value = 'addTop'
  labelDialogTitle.value = '添加顶层标签'
  labelForm.value = { name: '', description: '', color: '#409EFF', parent_id: null }
  labelDialogVisible.value = true
}

const openAddChildLabel = () => {
  labelDialogMode.value = 'addChild'
  labelDialogTitle.value = `在 "${currentNode.value.name}" 下添加子标签`
  labelForm.value = { name: '', description: '', color: '#409EFF', parent_id: currentNode.value.id }
  labelDialogVisible.value = true
}

const openEditLabel = () => {
  labelDialogMode.value = 'edit'
  labelDialogTitle.value = `编辑标签 "${currentNode.value.name}"`
  labelForm.value = {
    name: currentNode.value.name,
    description: currentNode.value.description || '',
    color: currentNode.value.color || '#409EFF',
    parent_id: currentNode.value.parent_id,
  }
  labelDialogVisible.value = true
}

const handleSaveLabel = async () => {
  if (!labelForm.value.name) {
    ElMessage.warning('标签名称不能为空')
    return
  }
  if (labelDialogMode.value === 'edit') {
    await updateLabel(currentNode.value.id, {
      name: labelForm.value.name,
      description: labelForm.value.description,
      color: labelForm.value.color,
      parent_id: labelForm.value.parent_id,
    })
    ElMessage.success('标签更新成功')
  } else {
    await createLabel(selectedGroupId.value, {
      name: labelForm.value.name,
      description: labelForm.value.description,
      color: labelForm.value.color,
      parent_id: labelForm.value.parent_id,
    })
    ElMessage.success('标签创建成功')
  }
  labelDialogVisible.value = false
  loadTree()
}

const handleDeleteLabel = async () => {
  try {
    await ElMessageBox.confirm(`删除标签 "${currentNode.value.name}"？子标签将变为顶层标签。`, '确认删除')
  } catch { return }
  await deleteLabel(currentNode.value.id)
  ElMessage.success('标签删除成功')
  currentNode.value = null
  loadTree()
}

onMounted(() => {
  loadGroups()
})
</script>
