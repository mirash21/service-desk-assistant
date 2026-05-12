# Модуль автоматизированной аналитики качества RAG системы

## 📋 Обзор

Модуль `rag_quality_analytics.py` предоставляет автоматизированную оценку качества RAG системы с использованием метрик RAGAS и сравнительный анализ параметра top_k.

### Возможности:

1. ✅ **Генерация тестовых вопросов** - автоматическое создание ground truth вопросов из базы знаний
2. ✅ **Метрики RAGAS** - оценка по 4 ключевым метрикам:
   - Faithfulness (Верность контексту)
   - Answer Relevance (Релевантность ответа)
   - Context Precision (Точность контекста)
   - Context Recall (Полнота контекста)
3. ✅ **A/B тестирование top_k** - сравнение результатов при разных значениях top_k (3, 5, 10)
4. ✅ **Визуализация результатов** - таблицы, графики, рекомендации
5. ✅ **Интеграция с Admin Panel** - удобный интерфейс для запуска и просмотра результатов
6. ✅ **Автоматизация** - возможность запуска через cron без блокировки основной работы

---

## 🚀 Быстрый старт

### Шаг 1: Применение миграции базы данных

```bash
# Подключитесь к Supabase и выполните миграцию
docker exec -i supabase-db psql -U postgres -d postgres < migrations/create_rag_quality_metrics_table.sql

# Или через Supabase Dashboard: SQL Editor → выполните SQL из файла миграции
```

### Шаг 2: Установка зависимостей (опционально)

Для использования полноценных метрик RAGAS:

```bash
docker exec max-bot-webhook pip install ragas langchain-openai langchain-community datasets
```

**Примечание:** Без RAGAS модуль будет работать в fallback режиме с базовыми эвристиками.

### Шаг 3: Запуск оценки

```bash
# Базовый запуск (50 вопросов, top_k = 3,5,10)
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py

# С кастомными параметрами
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py --sample 100 --top-k 3,5,10,15
```

### Шаг 4: Просмотр результатов в Admin Panel

Откройте Admin Panel и перейдите на вкладку **"🔬 RAG Quality Analytics"**

---

## 📊 Использование

### Командная строка

#### Базовый запуск:
```bash
python3 scripts/rag_quality_analytics.py
```

#### С параметрами:
```bash
# 100 тестовых вопросов, тестирование top_k = 3, 5, 10
python3 scripts/rag_quality_analytics.py --sample 100 --top-k 3,5,10

# 30 вопросов, только top_k = 5
python3 scripts/rag_quality_analytics.py --sample 30 --top-k 5
```

#### Через Docker:
```bash
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py --sample 50 --top-k 3,5,10
```

### Admin Panel

1. Откройте Admin Panel: `http://localhost:8501`
2. Перейдите на вкладку **"🔬 RAG Quality Analytics"**
3. Выберите параметры:
   - Количество тестовых вопросов (10-200)
   - Значения top_k для тестирования
4. Нажмите **"🚀 Запустить оценку"**
5. Дождитесь завершения (может занять несколько минут)
6. Просмотрите результаты на вкладке **"📈 Текущие результаты"**

---

## 📈 Интерпретация результатов

### Метрики RAGAS

| Метрика | Описание | Диапазон | Цель |
|---------|----------|----------|------|
| **Faithfulness** | Верность ответа контексту | 0-1 | >0.8 |
| **Answer Relevance** | Релевантность ответа вопросу | 0-1 | >0.8 |
| **Context Precision** | Точность выбранных контекстов | 0-1 | >0.7 |
| **Context Recall** | Полнота охвата информации | 0-1 | >0.7 |

### Выбор оптимального top_k

Модуль автоматически рекомендует оптимальное значение top_k на основе composite score:

```
Composite Score = (Faithfulness + Answer Relevance + Context Precision + Context Recall) / 4
```

**Пример вывода:**
```
💡 РЕКОМЕНДАЦИЯ:
   Оптимальное значение top_k = 5
   Средний score: 0.847
```

### Trade-offs при выборе top_k

| Top-K | Преимущества | Недостатки |
|-------|-------------|------------|
| **3** | Быстрее, меньше шума | Может пропустить важную информацию |
| **5** | Баланс точности и полноты | Среднее время ответа |
| **10** | Больше информации | Больше шума, медленнее |

---

## 🗄️ Хранение результатов

### Файловая система

Результаты сохраняются в папке `data/rag_analytics/`:

- `rag_evaluation_YYYYMMDD_HHMMSS.json` - полные результаты в JSON
- `rag_evaluation_details_YYYYMMDD_HHMMSS.csv` - детальные данные в CSV
- `test_questions.json` - сгенерированные тестовые вопросы

### Supabase Database

Сводные результаты сохраняются в таблицу `rag_quality_metrics`:

```sql
SELECT * FROM rag_quality_metrics 
ORDER BY evaluated_at DESC 
LIMIT 10;
```

**Структура таблицы:**
- `id` - UUID записи
- `top_k` - значение top_k
- `avg_faithfulness` - средняя верность
- `avg_answer_relevance` - средняя релевантность
- `avg_context_precision` - средняя точность контекста
- `avg_context_recall` - средняя полнота контекста
- `total_questions` - количество вопросов
- `avg_evaluation_time` - среднее время оценки (сек)
- `evaluated_at` - дата оценки

---

## ⚙️ Автоматизация

### Cron job для регулярной оценки

Добавьте в crontab для еженедельной оценки:

```bash
# Откройте crontab
crontab -e

# Добавьте запись (каждое воскресенье в 2:00 AM)
0 2 * * 0 cd /home/mirash/service-desk-assistant && \
  docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py \
  >> logs/rag_quality.log 2>&1
```

### Логирование

Логи сохраняются в `logs/rag_quality.log`:

```bash
# Просмотр логов
tail -f logs/rag_quality.log

# Поиск ошибок
grep "ERROR" logs/rag_quality.log
```

---

## 🔧 Настройка и кастомизация

### Интеграция с RAG Retriever

В файле `scripts/rag_quality_analytics.py` найдите метод `_get_rag_response` и замените заглушку на реальную интеграцию:

```python
def _get_rag_response(self, question: str, top_k: int = 5) -> tuple:
    """Получает ответ от RAG системы"""
    
    # Интеграция с вашим RAG retriever
    from rag.supabase_manager import SupabaseRAGManager
    
    rag = SupabaseRAGManager()
    answer, contexts = rag.query(question, top_k=top_k)
    
    return answer, contexts
```

### Добавление новых метрик

Чтобы добавить новые метрики RAGAS:

1. Импортируйте метрику в `RAGEvaluator`:
```python
from ragas.metrics import context_entity_recall
```

2. Добавьте в evaluation:
```python
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevance, context_precision, context_recall, context_entity_recall]
)
```

3. Обновите dataclass `EvaluationResult`:
```python
@dataclass
class EvaluationResult:
    # ... existing fields ...
    context_entity_recall: float
```

### Кастомные значения top_k

По умолчанию тестируются top_k = [3, 5, 10]. Для изменения:

```bash
# Командная строка
python3 scripts/rag_quality_analytics.py --top-k 2,4,6,8,10

# Admin Panel
# Введите значения через запятую в поле "Значения top_k для тестирования"
```

---

## 🐛 Решение проблем

### Ошибка: "No module named 'ragas'"

**Решение:** Установите библиотеку RAGAS или используйте fallback режим:

```bash
# Установка RAGAS
docker exec max-bot-webhook pip install ragas langchain-openai langchain-community datasets

# Или используйте fallback (без установки)
# Модуль автоматически переключится на базовые эвристики
```

### Ошибка: "relation rag_quality_metrics does not exist"

**Решение:** Примените миграцию базы данных:

```bash
# Через Supabase Dashboard:
# 1. Откройте SQL Editor
# 2. Скопируйте содержимое migrations/create_rag_quality_metrics_table.sql
# 3. Выполните SQL

# Или через psql:
docker exec -i supabase-db psql -U postgres -d postgres < migrations/create_rag_quality_metrics_table.sql
```

### Оценка занимает слишком много времени

**Решение:** Уменьшите количество тестовых вопросов:

```bash
# Вместо 100 вопросов используйте 30
python3 scripts/rag_quality_analytics.py --sample 30
```

### Низкие показатели метрик (<0.6)

**Диагностика:**

1. **Низкий Faithfulness:**
   - Проверьте качество чанков на противоречия
   - Убедитесь что ответы генерируются на основе контекста
   
2. **Низкий Answer Relevance:**
   - Улучшите prompt engineering
   - Проверьте качество embeddings
   
3. **Низкий Context Precision:**
   - Оптимизируйте стратегию поиска
   - Увеличьте размер chunk overlap
   
4. **Низкий Context Recall:**
   - Увеличьте базу знаний
   - Улучшите chunking strategy

---

## 📚 Архитектура модуля

### Компоненты:

1. **TestQuestionGenerator** - генерация тестовых вопросов из документов
2. **RAGEvaluator** - оценка качества с метриками RAGAS
3. **TopKComparator** - сравнительный анализ разных top_k
4. **ResultsStorage** - сохранение результатов (JSON, CSV, Supabase)

### Data Flow:

```
Documents → TestQuestionGenerator → Test Questions
                                    ↓
TopKComparator → RAG Response (different top_k)
                    ↓
              RAGEvaluator → Metrics
                    ↓
            ResultsStorage → JSON/CSV/Supabase
                    ↓
            Admin Panel → Visualization
```

---

## 📊 Примеры использования

### Пример 1: Базовая оценка

```bash
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py
```

**Результат:**
```
================================================================================
СРАВНИТЕЛЬНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ
================================================================================

Top-K    Faith.     Relev.     Prec.      Recall     Questions    Avg Time  
--------------------------------------------------------------------------------
3        0.823      0.856      0.745      0.712      50           2.34s     
5        0.847      0.871      0.768      0.734      50           3.12s     
10       0.831      0.863      0.752      0.798      50           5.67s     

================================================================================

💡 РЕКОМЕНДАЦИЯ:
   Оптимальное значение top_k = 5
   Средний score: 0.805
================================================================================
```

### Пример 2: Расширенная оценка

```bash
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py \
  --sample 100 \
  --top-k 3,5,7,10,15
```

---

## 🎯 Best Practices

### 1. Регулярная оценка
- Запускайте оценку **еженедельно** для мониторинга качества
- Настройте cron job для автоматизации
- Сравнивайте результаты во времени для выявления трендов

### 2. Выбор размера выборки
- **Быстрая проверка:** 20-30 вопросов (~2-3 минуты)
- **Стандартная оценка:** 50 вопросов (~5-7 минут)
- **Детальный анализ:** 100+ вопросов (~10-15 минут)

### 3. Интерпретация результатов
- Смотрите на **composite score**, а не на отдельные метрики
- Учитывайте **время ответа** (avg_evaluation_time)
- Ищите **баланс** между точностью и производительностью

### 4. Действия при ухудшении качества
1. Проверьте recent changes в базе знаний
2. Проанализируйте unanswered questions
3. Запустите диагностику чанков (scripts/comprehensive_rag_analysis.py)
4. При необходимости переобучите embeddings

---

## 🔗 Связанные файлы

- `scripts/rag_quality_analytics.py` - основной скрипт оценки
- `admin_panel/pages/3_🔬_RAG_Quality_Analytics.py` - страница Admin Panel
- `migrations/create_rag_quality_metrics_table.sql` - миграция базы данных
- `data/rag_analytics/` - папка с результатами
- `utils/document_validator.py` - валидатор документов (используется для генерации вопросов)

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `logs/rag_quality.log`
2. Убедитесь что таблица `rag_quality_metrics` создана
3. Проверьте зависимости: `pip list | grep ragas`
4. Обратитесь к документации RAGAS: https://docs.ragas.io

---

**Дата создания:** 11 мая 2026  
**Версия:** 1.0  
**Автор:** Service Desk Assistant Team
