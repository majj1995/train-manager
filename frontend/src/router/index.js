import { createRouter, createWebHistory } from 'vue-router'
import Images from '../views/Images.vue'
import Labeling from '../views/Labeling.vue'
import Preprocess from '../views/Preprocess.vue'
import Corpus from '../views/Corpus.vue'

const routes = [
  { path: '/', redirect: '/images' },
  { path: '/images', component: Images },
  { path: '/labeling', component: Labeling },
  { path: '/preprocess', component: Preprocess },
  { path: '/corpus', component: Corpus },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router