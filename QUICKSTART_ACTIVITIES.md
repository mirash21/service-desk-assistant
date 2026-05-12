# Быстрый старт: Настройка раздела Activities

## ⚡ Быстрая настройка (5 минут)

### 1. Примените миграцию базы данных

Откройте [Supabase SQL Editor](https://app.supabase.com/project/_/sql) и выполните:

```sql
CREATE TABLE IF NOT EXISTS chat_history (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  message_type TEXT NOT NULL CHECK (message_type IN ('user', 'bot')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_time ON chat_history(user_id, created_at DESC);
```

### 2. Перезапустите бота

```bash
cd /home/mirash/service-desk-assistant
docker compose restart max-bot-webhook
```

### 3. Откройте панель администратора

```bash
cd /home/mirash/service-desk-assistant/admin_panel
streamlit run app.py
```

Или через Docker:
```bash
docker compose up admin-panel
```

### 4. Перейдите на страницу «💬 Деятельность»

Готово! 🎉

---

## ✅ Проверка работы

1. Отправьте несколько сообщений боту через MAX Messenger
2. Обновите страницу Activities в панели администратора
3. Вы должны увидеть историю диалогов

## 📋 Что отслеживается

- ✅ Текстовые сообщения
- ✅ Голосовые сообщения (распознанный текст)
- ✅ Изображения (с описанием)
- ✅ Команды бота (/start, /voice, и т.д.)
- ✅ Ответы бота (все типы)

## 🔍 Возможности страницы

- Фильтрация по пользователям
- Просмотр полных диалогов
- Статистика активности
- Индикаторы типов сообщений (🖼️ 🎤 ⚙️ 🎫)
- Просмотр метаданных
- Пагинация

## 🐛 Проблемы?

Смотрите полную документацию: `ACTIVITIES_SETUP.md`
