import axios from 'axios'

// 统一走同源 /api 前缀（开发由 Vite 反代、生产由 Nginx 反代到后端 8000）
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export default api
