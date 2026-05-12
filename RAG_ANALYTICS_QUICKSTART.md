# Быстрый старт: Модуль аналитики качества RAG

## 🚀 3 шага для начала работы

### Шаг 1: Создание таблицы в Supabase

Откройте **Supabase Dashboard** → **SQL Editor** и выполните следующий SQL:

```sql
CREATE TABLE IF NOT EXISTS rag_quality_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    top_k INTEGER NOT NULL,
    avg_faithfulness FLOAT NOT NULL,
    avg_answer_relevance FLOAT NOT NULL,
    avg_context_precision FLOAT NOT NULL,
    avg_context_recall FLOAT NOT NULL,
    total_questions INTEGER NOT NULL,
    avg_evaluation_time FLOAT NOT NULL,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_metrics_top_k ON rag_quality_metrics(top_k);
CREATE INDEX IF NOT EXISTS idx_rag_metrics_evaluated_at ON rag_quality_metrics(evaluated_at DESC);
```

### Шаг 2: Запуск первой оценки

```bash
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py
```

**Что произойдет:**
- Сгенерируется 50 тестовых вопросов из базы знаний
- Запустится оценка с top_k = 3, 5, 10
- Результаты сохранятся в `data/rag_analytics/` и Supabase
- Выведется сравнительная таблица с рекомендацией

**Время выполнения:** ~5-7 минут

### Шаг 3: Просмотр результатов

Откройте Admin Panel: `http://localhost:8501`

Перейдите на вкладку **"🔬 RAG Quality Analytics"**

Вы увидите:
- 📈 Сравнительную таблицу метрик для разных top_k
- 📊 График изменения метрик
- 💡 Рекомендацию оптимального значения top_k
- 📚 Документацию по метрикам

---

## 📋 Пример вывода

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

---

## ⚙️ Кастомизация

### Изменение количества вопросов

```bash
# 100 вопросов вместо 50
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py --sample 100
```

### Тестирование других значений top_k

```bash
# top_k = 2, 4, 6, 8
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py --top-k 2,4,6,8
```

### Комбинированные параметры

```bash
# 80 вопросов с top_k = 3, 5, 7, 10
docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py --sample 80 --top-k 3,5,7,10
```

---

## 🔄 Автоматизация (Cron)

Для еженедельной оценки добавьте в crontab:

```bash
crontab -e

# Каждое воскресенье в 2:00 AM
0 2 * * 0 cd /home/mirash/service-desk-assistant && \
  docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py \
  >> logs/rag_quality.log 2>&1
```

---

## 📊 Интерпретация результатов

### Хорошие показатели ✅
- Все метрики > 0.8
- Минимальная разница между top_k
- Стабильные результаты во времени

### Требует внимания ⚠️
- Любая метрика < 0.6
- Большая вариативность между top_k
- Ухудшение со временем

### Действия при низких показателях

| Метрика | Проблема | Решение |
|---------|----------|---------|
| Faithfulness < 0.7 | Галлюцинации в ответах | Проверьте качество чанков |
| Answer Relevance < 0.7 | Нерелевантные ответы | Улучшите prompt engineering |
| Context Precision < 0.6 | Много шума в контекстах | Оптимизируйте embeddings |
| Context Recall < 0.6 | Пропуск важной информации | Увеличьте базу знаний |

---

## 📁 Где находятся результаты

### Файлы
- `data/rag_analytics/rag_evaluation_*.json` - полные результаты
- `data/rag_analytics/rag_evaluation_details_*.csv` - детальные данные
- `data/test_questions.json` - тестовые вопросы

### База данных
```sql
-- Последние 10 оценок
SELECT * FROM rag_quality_metrics 
ORDER BY evaluated_at DESC 
LIMIT 10;

-- Средние метрики по top_k
SELECT top_k, 
       AVG(avg_faithfulness) as avg_faith,
       AVG(avg_answer_relevance) as avg_rel,
       COUNT(*) as eval_count
FROM rag_quality_metrics 
GROUP BY top_k;
```

---

## ❓ FAQ

**Q: Сколько времени занимает оценка?**  
A: Зависит от количества вопросов. ~5-7 минут для 50 вопросов.

**Q: Можно ли прервать оценку?**  
A: Да, Ctrl+C. Частичные результаты не сохраняются.

**Q: Нужно ли устанавливать RAGAS?**  
A: Нет, модуль работает в fallback режиме без RAGAS. Для полноценных метрик: `pip install ragas`

**Q: Как часто запускать оценку?**  
A: Рекомендуется еженедельно или после значительных изменений в базе знаний.

**Q: Что делать если все метрики низкие?**  
A: Запустите `scripts/comprehensive_rag_analysis.py` для диагностики качества базы знаний.

---

## 📚 Дополнительная информация

- Полная документация: `RAG_QUALITY_ANALYTICS_README.md`
- Исходный код: `scripts/rag_quality_analytics.py`
- Admin Panel: страница `3_🔬_RAG_Quality_Analytics.py`

---

**Готово!** Теперь вы можете мониторить качество RAG системы автоматически. 🎉
