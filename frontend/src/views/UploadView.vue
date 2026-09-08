<template>
  <div>
    <h2>上传会议录音</h2>
    <form @submit.prevent="submit">
      <div style="margin-bottom: 10px">
        <input
          type="text"
          v-model="title"
          placeholder="会议标题（可选，默认用文件名）"
          style="width: 100%; padding: 8px"
        />
      </div>
      <div style="margin-bottom: 10px">
        <input type="file" accept="audio/*" @change="onFile" />
      </div>
      <button type="submit" :disabled="!file || uploading">
        {{ uploading ? '上传中…' : '上传并转写' }}
      </button>
    </form>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const title = ref('')
const file = ref(null)
const uploading = ref(false)
const error = ref('')

function onFile(e) {
  file.value = e.target.files[0] || null
}

async function submit() {
  if (!file.value) return
  uploading.value = true
  error.value = ''
  const fd = new FormData()
  fd.append('file', file.value)
  if (title.value.trim()) fd.append('title', title.value.trim())
  try {
    const { data } = await api.post('/meetings', fd)
    if (data.code === 0) {
      router.push(`/meetings/${data.data.meeting_id}`)
    } else {
      error.value = data.message
    }
  } catch (e) {
    error.value = e?.response?.data?.message || e.message
  } finally {
    uploading.value = false
  }
}
</script>
