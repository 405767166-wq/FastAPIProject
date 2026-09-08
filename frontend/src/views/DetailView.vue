<template>
  <div v-if="m">
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h2>{{ m.title }}</h2>
      <button class="del" @click="remove">删除会议</button>
    </div>
    <p>状态：<b>{{ m.status }}</b> ｜ 进度：{{ m.progress }}% ｜ 阶段：{{ m.stage }}</p>
    <div class="bar"><div class="fill" :style="{ width: m.progress + '%' }"></div></div>

    <div v-if="m.status === 'failed'" class="err" style="margin-top: 12px">
      处理失败：{{ m.error_message }}
    </div>

    <div v-if="m.status === 'completed'">
      <h3>转写全文</h3>
      <p class="transcript">{{ m.transcript }}</p>

      <h3>词频 Top</h3>
      <ul>
        <li v-for="w in words" :key="w.word">{{ w.word }}：{{ w.freq }}</li>
      </ul>

      <h3>会议纪要</h3>
      <pre class="summary">{{ summary }}</pre>
    </div>
  </div>
  <p v-else>加载中…</p>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const m = ref(null)
const words = ref([])
const summary = ref('')
let timer = null

async function remove() {
  if (!window.confirm('确认删除该会议吗？此操作不可恢复。')) return
  try {
    await api.delete(`/meetings/${route.params.id}`)
    router.push('/meetings')
  } catch (e) {
    window.alert(e?.response?.data?.message || '删除失败')
  }
}

async function poll() {
  try {
    const { data } = await api.get(`/meetings/${route.params.id}`)
    m.value = data.data
    if (data.data.status === 'completed') {
      clearInterval(timer)
      const [w, s] = await Promise.all([
        api.get(`/meetings/${route.params.id}/words?top=20`),
        api.get(`/meetings/${route.params.id}/summary`),
      ])
      words.value = w.data.data.items
      summary.value = s.data.data.summary
    }
  } catch (e) {
    /* 加载失败（如 404）先忽略，下轮继续 */
  }
}

onMounted(() => {
  poll()
  timer = setInterval(poll, 2000) // 每 2 秒轮询进度
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.del {
  color: #dc2626;
  border-color: #dc2626;
}
</style>
