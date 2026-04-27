# 🚀 Быстрый старт - Docker Deployment

## ✅ Что было сделано

1. ✅ Проект клонирован из GitHub
2. ✅ Docker-образ успешно собран
3. ✅ Контейнер настроен и готов к запуску

## 📋 Необходимые шаги для запуска

### Шаг 1: Настройка переменных окружения

Откройте файл `.env` и заполните следующие параметры:

```bash
nano .env
```

Необходимые переменные:

```env
# MAX Messenger (получите токен в https://dev.max.ru/)
MAX_BOT_TOKEN=ваш_токен_max_bot

# Webhook URL (оставьте пустым для Long Polling)
WEBHOOK_URL=https://vaib-cod.ru/webhook

# Yandex AI Studio (получите ключ в https://cloud.yandex.ru/services/yandexgpt)
YANDEX_API_KEY=ваш_yandex_api_key
YANDEX_FOLDER_ID=b1gfa70gk1jptiabg9eg

# Supabase (настройте в https://supabase.com/)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=ваш_supabase_anon_key
```

### Шаг 2: Запуск контейнера

```bash
cd /home/mirash/service-desk-assistant
docker compose up -d
```

### Шаг 3: Проверка статуса

```bash
# Проверить статус контейнера
docker compose ps

# Просмотреть логи
docker compose logs -f

# Проверить здоровье контейнера
docker inspect --format='{{.State.Health.Status}}' service-desk-bot
```

## 🔧 Управление контейнером

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Просмотр логов в реальном времени
docker compose logs -f --tail=100

# Обновление образа
git pull
docker compose build
docker compose up -d
```

## 📊 Мониторинг

```bash
# Использование ресурсов
docker stats service-desk-bot

# Логи приложения
docker compose logs -f service-desk-bot

# Проверка webhook endpoint
curl http://localhost:8080/health
```

## ⚠️ Решение проблем

### Контейнер не запускается

```bash
# Проверьте логи на наличие ошибок
docker compose logs service-desk-bot

# Убедитесь, что все переменные окружения настроены
docker compose exec service-desk-bot env | grep -E "MAX_BOT|YANDEX|SUPABASE"
```

### Webhook не работает

```bash
# Проверьте доступность webhook
curl http://localhost:8080/webhook

# Проверьте настройки nginx (если используется)
sudo tail -f /var/log/nginx/error.log
```

### Проблемы с подключением к базе данных

```bash
# Проверьте подключение к Supabase
docker compose exec service-desk-bot python check_system.py
```

## 🌐 Настройка Nginx (опционально)

Если вы хотите использовать webhook через домен `vaib-cod.ru`, настройте nginx:

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
    }
}
```

Затем настройте SSL с помощью Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vaib-cod.ru
```

## 📁 Структура проекта

```
service-desk-assistant/
├── Dockerfile              # Конфигурация Docker образа
├── docker-compose.yml      # Docker Compose конфигурация
├── .env                    # Переменные окружения (создайте из .env.example)
├── .env.example            # Пример конфигурации
├── main.py                 # Точка входа приложения
├── requirements.txt        # Python зависимости
├── logs/                   # Логи приложения (volume)
├── data/                   # Данные базы знаний (volume)
└── temp/                   # Временные файлы (volume)
```

## 🔐 Безопасность

- Никогда не коммитьте файл `.env` в Git
- Используйте сильные пароли и API ключи
- Регулярно обновляйте образ: `docker compose pull && docker compose up -d`
- Настройте firewall для ограничения доступа к порту 8080

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose logs -f`
2. Убедитесь, что все переменные окружения настроены правильно
3. Проверьте документацию: [DEPLOY.md](DEPLOY.md), [README_DOCKER.md](README_DOCKER.md)

## ✨ Готово!

После настройки всех переменных окружения запустите:

```bash
docker compose up -d
```

Бот готов к работе! 🎉
