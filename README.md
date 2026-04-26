# 🤖 Service Desk Assistant

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Мультимодальный AI-ассистент для сервис-деска с поддержкой текста, голоса и изображений**

[Возможности](#-возможности) • [Установка](#-установка) • [Документация](#-документация) • [Деплой](#-деплой) • [Contributing](#-contributing)

</div>

---

## 📋 Описание

Service Desk Assistant — это интеллектуальный бот для автоматизации службы поддержки, использующий передовые технологии искусственного интеллекта. Бот способен понимать и обрабатывать запросы пользователей в различных форматах: текст, голосовые сообщения и изображения.

### ✨ Ключевые особенности

- 🎯 **Автоматическая классификация заявок** — AI анализирует обращения и определяет категорию, приоритет и срочность
- 🗣️ **Голосовое взаимодействие** — распознавание речи (STT) и синтез голоса (TTS) на русском языке
- 👁️ **Анализ изображений** — OCR и компьютерное зрение для обработки скриншотов и фото ошибок
- 🧠 **RAG система** — семантический поиск по базе знаний с использованием векторных эмбеддингов
- 🔄 **Гибкие режимы работы** — поддержка Webhook и Long Polling для интеграции с MAX Messenger
- 🐳 **Docker-ready** — готов к развертыванию в продакшене
- 📊 **Полное логирование** — детальное отслеживание всех операций
- ⚡ **Rate Limiting** — защита от перегрузки API

## 🛠️ Стек технологий

<div align="center">

| Категория | Технологии |
|-----------|------------|
| **Язык** | ![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white) |
| **AI/ML** | ![YandexGPT](https://img.shields.io/badge/YandexGPT-FFCC00?logo=yandex&logoColor=black) ![Embeddings](https://img.shields.io/badge/Vector%20Search-FF6B6B?logo=database&logoColor=white) |
| **База данных** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white) ![pgvector](https://img.shields.io/badge/pgvector-336791?logo=postgresql&logoColor=white) |
| **Контейнеризация** | ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white) |
| **Web** | ![aiohttp](https://img.shields.io/badge/aiohttp-2C5BB4?logo=python&logoColor=white) ![nginx](https://img.shields.io/badge/nginx-009639?logo=nginx&logoColor=white) |
| **Интеграции** | ![MAX Messenger](https://img.shields.io/badge/MAX_Messenger-0088CC?logo=telegram&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white) |

</div>

## 🚀 Возможности

### 1. Мультимодальная обработка

```
📝 Текст → Анализ тональности, извлечение сущностей, классификация
🎤 Голос → Распознавание речи → Текст → Обработка → Синтез ответа
🖼️ Изображения → OCR → Извлечение текста → Анализ контекста
```

### 2. RAG (Retrieval-Augmented Generation)

- Векторизация документов с помощью Yandex Embeddings
- Семантический поиск по базе знаний (cosine similarity)
- Контекстно-зависимые ответы на основе найденной информации
- Автоматическое обновление индекса при добавлении новых документов

### 3. Интеллектуальная маршрутизация

- Автоматическое определение категории заявки
- Оценка приоритета (Low/Medium/High/Critical)
- Назначение ответственного специалиста
- Эскалация критических инцидентов

### 4. Гибкая архитектура

- **Webhook mode** — мгновенная доставка сообщений через HTTP
- **Long Polling** — периодический опрос API для получения обновлений
- **Retry mechanism** — автоматические повторные попытки при ошибках
- **Graceful shutdown** — корректное завершение работы

## 📦 Установка

### Предварительные требования

- Python 3.12+
- Docker и Docker Compose (для контейнеризации)
- Аккаунты в сервисах:
  - [Yandex AI Studio](https://cloud.yandex.ru/services/yandexgpt)
  - [MAX Messenger](https://dev.max.ru/)
  - [Supabase](https://supabase.com/)

### Способ 1: Локальная установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-username/service-desk-assistant.git
cd service-desk-assistant

# 2. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env файл, добавив ваши API ключи

# 5. Инициализируйте базу данных
python init_db.py

# 6. Запустите бота
python main.py
```

### Способ 2: Docker (рекомендуется для продакшена)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-username/service-desk-assistant.git
cd service-desk-assistant

# 2. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env файл

# 3. Соберите и запустите контейнер
docker-compose up -d

# 4. Проверьте логи
docker-compose logs -f
```

## ⚙️ Конфигурация

Создайте файл `.env` на основе [.env.example](.env.example):

```env
# MAX Messenger
MAX_BOT_TOKEN=your_max_bot_token
WEBHOOK_URL=https://your-domain.ru/webhook  # Оставьте пустым для Long Polling

# Yandex AI Studio
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_folder_id

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### Режимы работы

**Webhook Mode** (рекомендуется для продакшена):
```env
WEBHOOK_URL=https://your-domain.ru/webhook
```

**Long Polling Mode** (для тестирования):
```env
# WEBHOOK_URL=  # Закомментируйте или оставьте пустым
```

## 📖 Использование

### Текстовые сообщения

```
Пользователь: "Не работает принтер в офисе 305"
Бот: 🎫 Создана заявка #1234
     Категория: Оборудование
     Приоритет: Средний
     Статус: В обработке
     
     Наш специалист свяжется с вами в течение 30 минут.
```

### Голосовые сообщения

```
🎤 Пользователь отправляет голосовое сообщение
   ↓
🔊 Yandex STT преобразует речь в текст
   ↓
🧠 AI анализирует запрос
   ↓
📝 Бот создает заявку и отвечает текстом или голосом
```

### Изображения

```
🖼️ Пользователь отправляет скриншот ошибки
   ↓
👁️ Yandex Vision извлекает текст и описывает изображение
   ↓
🧠 AI анализирует контекст
   ↓
📝 Создается заявка с прикрепленным изображением
```

## 🏗️ Архитектура проекта

```
service-desk-assistant/
├── handlers/              # Обработчики сообщений
│   └── message_handler.py
├── services/              # Сервисы интеграций
│   ├── yandex_service.py  # Yandex AI Studio
│   └── supabase_rag.py    # RAG система
├── utils/                 # Утилиты
│   ├── logger.py          # Логирование
│   ├── file_handler.py    # Работа с файлами
│   └── rate_limiter.py    # Rate limiting
├── rag/                   # RAG компоненты
│   └── supabase_manager.py
├── config.py              # Конфигурация
├── main.py                # Точка входа
├── webhook_server.py      # Webhook сервер
├── Dockerfile             # Docker образ
├── docker-compose.yml     # Docker Compose
└── requirements.txt       # Зависимости Python
```

## 🚀 Деплой

Подробная инструкция по развертыванию на сервере доступна в [DEPLOY.md](DEPLOY.md).

### Быстрый старт на сервере

```bash
# 1. Скопируйте файлы на сервер
scp -r * user@your-server:/opt/service-desk-bot/

# 2. Настройте .env файл на сервере
ssh user@your-server
cd /opt/service-desk-bot
nano .env

# 3. Запустите через Docker Compose
docker-compose up -d

# 4. Настройте nginx для webhook
sudo nano /etc/nginx/sites-available/service-desk
# (см. DEPLOY.md для конфигурации)
```

## 📊 Мониторинг

```bash
# Просмотр логов в реальном времени
docker-compose logs -f

# Статус контейнера
docker-compose ps

# Использование ресурсов
docker stats service-desk-bot

# Проверка здоровья
docker inspect --format='{{.State.Health.Status}}' service-desk-bot
```

## 🧪 Тестирование

```bash
# Проверка работоспособности системы
python check_system.py

# Тестирование подключения к Supabase
python test_supabase.py
```

## 🤝 Contributing

Мы приветствуем вклад в развитие проекта! 🎉

1. **Fork** репозиторий
2. Создайте ветку для вашей фичи (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте **Pull Request**

### Guidelines

- Следуйте [PEP 8](https://peps.python.org/pep-0008/) стилю кода
- Добавляйте docstrings ко всем функциям и классам
- Пишите тесты для нового функционала
- Обновляйте документацию при изменении API

## 📄 License

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.

## 👥 Авторы

- **Rashid Minshin** - *Initial work* - [MiRash](https://github.com/MiRash)

## 🙏 Благодарности

- [Yandex Cloud](https://cloud.yandex.ru/) - за предоставление мощных AI сервисов
- [MAX Messenger](https://dev.max.ru/) - за платформу для мессенджера
- [Supabase](https://supabase.com/) - за отличную BaaS платформу
- [OpenSource сообщество](https://opensource.org/) - за вдохновение и инструменты

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [Issues](https://github.com/your-username/service-desk-assistant/issues)
2. Создайте новый Issue с подробным описанием проблемы
3. Для срочных вопросов свяжитесь со мной напрямую

---

<div align="center">

**⭐ Если проект вам понравился, поставьте звезду!**

Made with ❤️ by Rashid Minshin

</div>
