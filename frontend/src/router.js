import { createRouter, createWebHistory } from 'vue-router'
import UploadView from './views/UploadView.vue'
import ListView from './views/ListView.vue'
import DetailView from './views/DetailView.vue'

const routes = [
  { path: '/', component: UploadView },
  { path: '/meetings', component: ListView },
  { path: '/meetings/:id', component: DetailView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
