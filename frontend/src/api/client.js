// frontend/src/api/client.js
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// ✅ Автоматически добавляет токен ко ВСЕМ запросам
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('moonrise_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;