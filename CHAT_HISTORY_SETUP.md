# Инструкция по созданию таблицы chat_history

## Проблема
Таблица `chat_history` не существует в базе данных Supabase, поэтому история чата не сохраняется и не извлекается.

## Решение

### Для self-hosted Supabase (ваш случай)

Если вы используете self-hosted Supabase (контейнеры Docker), таблица уже создана!
Просто перезапустите PostgREST для обновления кэша схемы:

```bash
docker restart supabase-rest
sleep 5
```

После этого проверьте:
```bash
docker exec -it max-bot-webhook python check_and_create_chat_history.py
```

Ожидаемый результат:
```
✅ Таблица chat_history существует
   Количество записей: X
```

### Для Supabase Cloud

1. Откройте [Supabase Dashboard](https://app.supabase.com)
2. Выберите ваш проект service-desk-assistant
3. Перейдите в **SQL Editor** (в левом меню)
4. Нажмите **New query**
5. Вставьте следующий SQL код и нажмите **Run**:

```sql
-- Миграция: Создание таблицы для хранения истории чатов
-- Дата: 2026-05-10
-- Описание: Добавляет таблицу chat_history для отслеживания диалогов пользователей с ботом

CREATE TABLE IF NOT EXISTS chat_history (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  message_type TEXT NOT NULL CHECK (message_type IN ('user', 'bot')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого поиска по пользователю и времени
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_time ON chat_history(user_id, created_at DESC);

-- Комментарий к таблице
COMMENT ON TABLE chat_history IS 'История сообщений между пользователями и ботом';
COMMENT ON COLUMN chat_history.user_id IS 'ID пользователя в MAX Messenger';
COMMENT ON COLUMN chat_history.message_type IS 'Тип сообщения: user (от пользователя) или bot (ответ бота)';
COMMENT ON COLUMN chat_history.content IS 'Содержимое сообщения';
COMMENT ON COLUMN chat_history.metadata IS 'Дополнительные метаданные (режим, наличие изображений и т.д.)';
COMMENT ON COLUMN chat_history.created_at IS 'Время создания сообщения';
```

### Шаг 2: Обновление кэша схемы PostgREST

**Для self-hosted Supabase:**
```bash
docker restart supabase-rest
sleep 5
```

**Для Supabase Cloud:**
Кэш обновляется автоматически, но можно форсировать через API:

**Вариант A: Через Docker (рекомендуется)**
```bash
docker exec -it max-bot-webhook python refresh_schema_cache.py
```

**Вариант B: Через REST API**
```bash
curl -X POST "YOUR_SUPABASE_URL/rest/v1/rpc/refresh_schema_cache" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY" \
  -H "Content-Type: application/json"
```

### Шаг 3: Проверка работы

После выполнения шагов 1-2 проверьте что таблица создана и работает:

```bash
docker exec -it max-bot-webhook python check_and_create_chat_history.py
```

Ожидаемый результат:
```
✅ Таблица chat_history найдена!
   Количество записей: X
```

### Шаг 4: Тестирование контекста разговора

Отправьте несколько сообщений боту подряд и проверьте логи:

```bash
docker logs max-bot-webhook --tail 50 | grep "Получено.*сообщений истории"
```

Ожидаемый результат:
```
INFO - Получено 2 сообщений истории для 63137852
INFO - Получено 4 сообщений истории для 63137852
```

## Что было исправлено

### Изменения в коде:

1. **rag/supabase_manager.py** - добавлен метод `get_chat_history()`
   - Извлекает последние N сообщений пользователя
   - Возвращает в формате `[{'role': 'user'/'assistant', 'content': '...'}]`

2. **handlers/message_handler.py** - обновлены все вызовы `build_rag_prompt()`
   - `_handle_question()` - строка 393
   - `_handle_image_question()` - строка 494
   - `_handle_content()` (RAG mode) - строки 619, 632, 811, 825
   - Теперь передают историю диалога в промпт

3. **utils/prompt_builder.py** - уже поддерживал параметр `conversation_history`
   - Форматирует историю в читаемый вид
   - Включает последние 3 сообщения в промпт

## Как это работает

```
Пользователь: "Как подключить принтер?"
    ↓
Сохраняется в chat_history (user message)
    ↓
Извлекается история (последние 5 сообщений)
    ↓
Поиск в RAG + формирование промпта с историей
    ↓
LLM генерирует ответ с учетом контекста
    ↓
Ответ сохраняется в chat_history (bot message)
    ↓
Отправляется пользователю
```

## Troubleshooting

### Ошибка: "Could not find the table 'public.chat_history' in the schema cache"

**Причина:** Таблица не создана ИЛИ кэш схемы не обновлен

**Решение:**
1. Убедитесь что таблица создана (Шаг 1)
2. Обновите кэш схемы (Шаг 2)
3. Перезапустите контейнер: `docker compose restart max-bot-webhook`

### История не извлекается

**Проверка:**
```bash
docker exec -it max-bot-webhook python -c "
from rag.supabase_manager import SupabaseRAGManager
rm = SupabaseRAGManager()
history = rm.get_chat_history('YOUR_USER_ID', limit=5)
print(f'Получено {len(history)} сообщений')
print(history)
"
```

### Сообщения не сохраняются

**Проверка логов:**
```bash
docker logs max-bot-webhook --tail 100 | grep "Ошибка сохранения истории"
```

Если есть ошибки - проверьте что таблица существует и имеет правильную структуру.

## Дополнительные ресурсы

- Migration файл: `migrations/002_create_chat_history.sql`
- Скрипт проверки: `check_and_create_chat_history.py`
- Скрипт обновления кэша: `refresh_schema_cache.py`
- Тестовый скрипт: `test_chat_context.py`
