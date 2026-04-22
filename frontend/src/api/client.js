// frontend/src/api/client.js
import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 15000, // 10 секунд — без этого запрос висит вечно при недоступном backend
});

// ✅ Автоматически добавляет токен ко ВСЕМ запросам
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('moonrise_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ✅ Глобальная обработка ошибок — prevents unhandled promise rejections
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('⏱️ API request timeout:', error.config?.url);
    } else if (error.code === 'ERR_NETWORK') {
      console.error('🌐 Network error (backend unreachable):', error.config?.url);
    }
    return Promise.reject(error);
  }
);

export default client;