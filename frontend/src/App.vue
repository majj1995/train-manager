<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <el-container style="height: 100vh">
    <el-header style="background: #409EFF; color: #fff; display: flex; align-items: center; padding: 0 20px">
      <span style="font-size: 18px; font-weight: bold; white-space: nowrap">Auto-Train 数据管理</span>
      <el-menu
        :default-active="router.currentRoute.value.path"
        mode="horizontal"
        :ellipsis="false"
        style="background: #409EFF; color: #fff; margin-left: 40px; border-bottom: none"
        text-color="#fff"
        active-text-color="#fff"
        @select="(path) => router.push(path)"
      >
        <el-menu-item index="/images">数据管理</el-menu-item>
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

<style>
body { margin: 0 }
.el-menu--horizontal > .el-menu-item { border-bottom: none !important }
.el-menu--horizontal > .el-menu-item.is-active { border-bottom: 2px solid #fff !important }
</style>