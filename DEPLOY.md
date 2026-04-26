# 🚀 Инструкция по деплою бота на сервер

## 📋 Требования

- Docker и Docker Compose установлены на сервере
- Доступ к серверу по SSH
- Домен `vaib-cod.ru` настроен на сервер

## 🔧 Шаги деплоя

### 1. Подготовка файлов на сервере

```bash
# Создайте директорию для проекта
mkdir -p /opt/service-desk-bot
cd /opt/service-desk-bot

# Скопируйте файлы проекта на сервер
scp -r * user@your-server:/opt/service-desk-bot/
```

### 2. Настройка переменных окружения

Создайте файл `.env` на сервере:

```bash
nano .env
```

Добавьте конфигурацию:

```env
# MAX Messenger
MAX_BOT_TOKEN=ваш_токен_max

# Webhook (оставьте пустым для Long Polling)
WEBHOOK_URL=https://vaib-cod.ru/webhook

# Yandex AI Studio
YANDEX_API_KEY=ваш_ключ_yandex
YANDEX_FOLDER_ID=b1gfa70gk1jptiabg9eg

# Supabase
SUPABASE_URL=https://supabase-api.vaib-cod.ru
SUPABASE_KEY=ваш_ключ_supabase
```

### 3. Сборка и запуск

```bash
# Сборка образа
docker-compose build

# Запуск контейнера
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### 4. Настройка Nginx

Добавьте в конфигурацию nginx (`/etc/nginx/sites-available/service-desk`):

```nginx
server {
    listen 80;
    server_name vaib-cod.ru;

    location /webhook {
        proxy_pass http://localhost:8080/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Для WebSocket (если понадобится)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/service-desk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Настройка SSL (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vaib-cod.ru
```

## 📊 Управление контейнером

```bash
# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление кода
git pull
docker-compose build
docker-compose up -d
```

## 🔍 Мониторинг

```bash
# Проверка здоровья контейнера
docker inspect --format='{{.State.Health.Status}}' service-desk-bot

# Использование ресурсов
docker stats service-desk-bot

# Логи в реальном времени
docker-compose logs -f --tail=100
```

## ⚠️ Решение проблем

### Бот не запускается
```bash
# Проверьте логи
docker-compose logs service-desk-bot

# Проверьте переменные окружения
docker-compose exec service-desk-bot env
```

### Webhook не работает
```bash
# Проверьте доступность webhook
curl https://vaib-cod.ru/webhook

# Проверьте nginx логи
sudo tail -f /var/log/nginx/error.log
```

### Проблемы с подключением к базе данных
```bash
# Проверьте подключение к Supabase
docker-compose exec service-desk-bot python check_system.py
```

## 🔄 Автоматическое обновление

Создайте cron job для автоматического обновления:

```bash
crontab -e

# Добавьие строку (обновление каждый день в 3:00)
0 3 * * * cd /opt/service-desk-bot && git pull && docker-compose up -d --build
```

## ✅ Готово!

Бот запущен и готов к работе! 🎉
