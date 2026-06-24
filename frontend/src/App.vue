<template>
  <el-container style="height: 100vh">
    <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e6e6e6">
      <h2 style="margin: 0">Auto-Train 数据管理</h2>
      <el-menu :default-active="currentRoute" mode="horizontal" router>
        <el-menu-item index="/images">数据管理</el-menu-item>
        <el-menu-item index="/labels">标签管理</el-menu-item>
        <el-menu-item index="/labeling">数据标注</el-menu-item>
        <el-menu-item index="/preprocess">预处理</el-menu-item>
        <el-menu-item index="/corpus">语料生成</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentRoute = computed(() => route.path)
</script>
