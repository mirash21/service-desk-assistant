# 🤖 Service Desk Assistant - Docker Deployment

## Быстрый старт

### Локальное тестирование

```bash
# Сборка образа
docker-compose build

# Запуск
docker-compose up
```

### Деплой на сервер

1. Скопируйте файлы на сервер
2. Настройте `.env` файл
3. Запустите: `docker-compose up -d`

Подробная инструкция: [DEPLOY.md](DEPLOY.md)

## Структура проекта

```
├── Dockerfile              # Конфигурация Docker образа
├── docker-compose.yml      # Docker Compose конфигурация
├── .dockerignore          # Исключения для Docker
├── deploy.sh              # Скрипт деплоя (Linux/Mac)
├── deploy.ps1             # Скрипт деплоя (Windows)
├── DEPLOY.md              # Подробная инструкция по деплою
└── ...
```

## Команды управления

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление
docker-compose pull
docker-compose up -d
```

## Порты

- **8080** - Webhook endpoint (`/webhook`)

## Переменные окружения

Создайте файл `.env`:

```env
MAX_BOT_TOKEN=your_token
WEBHOOK_URL=https://vaib-cod.ru/webhook
YANDEX_API_KEY=your_key
YANDEX_FOLDER_ID=b1gfa70gk1jptiabg9eg
SUPABASE_URL=https://supabase-api.vaib-cod.ru
SUPABASE_KEY=your_supabase_key
```

## Health Check

Контейнер автоматически проверяет здоровье каждые 30 секунд:

```bash
docker inspect --format='{{.State.Health.Status}}' service-desk-bot
```

## Тома (Volumes)

Данные сохраняются в следующих директориях:

- `./logs` - Логи приложения
- `./data` - Данные базы знаний
- `./temp` - Временные файлы

## Поддержка

При возникновении проблем смотрите логи:

```bash
docker-compose logs -f --tail=100
```
