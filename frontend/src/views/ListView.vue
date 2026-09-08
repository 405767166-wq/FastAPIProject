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

onMounted(load)
</script>
