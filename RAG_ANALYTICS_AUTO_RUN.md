# 🚀 RAG Quality Analytics - Полностью автоматический запуск

## ✅ Что реализовано:

Теперь вы можете запускать оценку качества RAG системы **одной кнопкой** прямо из Admin Panel, без необходимости открывать терминал!

---

## 🎯 Как использовать:

### Шаг 1: Откройте Admin Panel
```
http://localhost:8501
```

### Шаг 2: Перейдите на вкладку "🔬 RAG Quality Analytics"

### Шаг 3: Настройте параметры (опционально)
- Количество тестовых вопросов: по умолчанию 50
- Значения top_k для сравнения: по умолчанию 3,5,10

### Шаг 4: Нажмите кнопку "🚀 Запустить оценку"

### Шаг 5: Подождите 5-10 минут
- Прогресс-бар показывает статус выполнения
- Оценка выполняется в фоновом режиме

### Шаг 6: Обновите страницу
После завершения оценки обновите страницу браузера (F5) и перейдите на вкладку "📈 Текущие результаты" чтобы увидеть графики и таблицы.

---

## 🔧 Архитектура решения:

### Компоненты:

1. **API Server** (`scripts/rag_analytics_api.py`)
   - Запущен в контейнере `max-bot-webhook` на порту 8766
   - Принимает POST запросы от Admin Panel
   - Запускает скрипт оценки в фоновом потоке
   - Endpoint: `POST http://max-bot-webhook:8766/run-evaluation`

2. **Admin Panel** (`admin_panel/pages/4_🔬_RAG_Quality_Analytics.py`)
   - Streamlit интерфейс с кнопкой запуска
   - Отправляет HTTP запрос на API сервер
   - Показывает прогресс-бар во время выполнения
   - Читает результаты из Supabase для отображения

3. **Analytics Script** (`scripts/rag_quality_analytics.py`)
   - Генерирует тестовые вопросы из базы знаний
   - Запускает оценку с разными top_k значениями
   - Рассчитывает метрики RAGAS
   - Сохраняет результаты в JSON, CSV и Supabase

---

## 📊 Метрики качества:

Оценка рассчитывает 4 ключевые метрики:

1. **Faithfulness** (Верность контексту) - 0.0-1.0
2. **Answer Relevance** (Релевантность ответа) - 0.0-1.0
3. **Context Precision** (Точность контекста) - 0.0-1.0
4. **Context Recall** (Полнота контекста) - 0.0-1.0

Система автоматически рекомендует оптимальное значение top_k на основе composite score.

---

## 🔍 Troubleshooting:

### Проблема: Кнопка не работает / Ошибка подключения

**Решение:** Проверьте что API сервер запущен:
```bash
docker exec max-bot-webhook python3 -c "
import urllib.request
response = urllib.request.urlopen('http://localhost:8766/health')
print(response.read().decode())
"
```

Если не работает, перезапустите API сервер:
```bash
docker exec -d max-bot-webhook python3 /app/scripts/rag_analytics_api.py
```

### Проблема: Результаты не отображаются

**Решение:** 
1. Убедитесь что таблица `rag_quality_metrics` создана в Supabase
2. Проверьте логи контейнера max-bot-webhook:
```bash
docker logs max-bot-webhook --tail 50 | grep -i "оценка\|analytics"
```

### Проблема: Долгое выполнение (>15 минут)

**Решение:** Уменьшите количество тестовых вопросов до 20-30 для быстрой проверки.

---

## 📁 Файлы:

- `/home/mirash/service-desk-assistant/scripts/rag_analytics_api.py` - API сервер
- `/home/mirash/service-desk-assistant/scripts/rag_quality_analytics.py` - Скрипт оценки
- `/home/mirash/service-desk-assistant/admin_panel/pages/4_🔬_RAG_Quality_Analytics.py` - UI страница
- `/home/mirash/service-desk-assistant/data/rag_analytics/` - Результаты (JSON/CSV)

---

## 🎉 Готово!

Теперь вы можете мониторить качество RAG системы без единой команды в терминале! Просто нажмите кнопку в браузере! 🚀
