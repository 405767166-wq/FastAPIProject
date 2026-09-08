<template>
  <div>
    <h2>历史会议</h2>
    <button @click="load">刷新</button>
    <table v-if="items.length" style="margin-top: 12px">
      <thead>
        <tr>
          <th>标题</th>
          <th>状态</th>
          <th>进度</th>
          <th>创建时间</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in items" :key="m.meeting_id">
          <td>{{ m.title }}</td>
          <td>{{ m.status }}</td>
          <td>{{ m.progress }}%</td>
          <td>{{ m.created_at }}</td>
          <td>
            <router-link :to="`/meetings/${m.meeting_id}`">查看</router-link>
            <button class="del" @click="remove(m)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>暂无记录</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const items = ref([])

async function load() {
  try {
    const { data } = await api.get('/meetings')
    items.value = data.data.items
  } catch (e) {
    items.value = []
  }
}

async function remove(m) {
  if (!window.confirm(`确认删除「${m.title}」吗？此操作不可恢复。`)) return
  try {
    const { data } = await api.delete(`/meetings/${m.meeting_id}`)
    if (data.code === 0) {
      load()
    } else {
      window.alert(data.message)
    }
  } catch (e) {
    window.alert(e?.response?.data?.message || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.del {
  margin-left: 10px;
  color: #dc2626;
  border-color: #dc2626;
}
</style>
