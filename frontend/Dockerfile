FROM node:20-alpine

WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package.json package-lock.json ./
RUN npm ci

# Копируем код
COPY . .

# Открываем порт
EXPOSE 5173

# Запуск dev сервера
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]