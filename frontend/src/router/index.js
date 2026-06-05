import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/images' },
  { path: '/images', name: 'Images', component: () => import('../views/Images.vue') },
  { path: '/labeling', name: 'Labeling', component: () => import('../views/Labeling.vue') },
  { path: '/preprocess', name: 'Preprocess', component: () => import('../views/Preprocess.vue') },
  { path: '/corpus', name: 'Corpus', component: () => import('../views/Corpus.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router