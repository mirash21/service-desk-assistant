# Быстрый старт

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Настройка конфигурации

```bash
# Скопируйте шаблон
cp .env.example .env

# Откройте .env и заполните параметры:
# - MAX_BOT_TOKEN
# - YANDEX_API_KEY  
# - SUPABASE_KEY
```

## 3. Проверка системы

```bash
python check_system.py
```

Этот скрипт проверит:
- ✅ Конфигурацию
- ✅ Подключение к Yandex API
- ✅ Подключение к Supabase
- ✅ Наличие всех директорий

## 4. Инициализация базы данных

```bash
python init_db.py
```

Или выполните SQL вручную через Supabase Studio.

## 5. Запуск бота

```bash
python main.py
```

## Готово! 🎉

Бот запущен и ожидает сообщения.

---

**Полезные команды:**
- `/start` - начать работу
- `/help` - помощь
- `/mode text|rag|voice` - переключить режим
- `/stats` - статистика БД
- `/index` - индексировать документы
