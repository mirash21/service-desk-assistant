-- Миграция для создания таблицы хранения метрик качества RAG
-- Используется модулем rag_quality_analytics.py

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

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_rag_metrics_top_k ON rag_quality_metrics(top_k);
CREATE INDEX IF NOT EXISTS idx_rag_metrics_evaluated_at ON rag_quality_metrics(evaluated_at DESC);

-- Комментарии
COMMENT ON TABLE rag_quality_metrics IS 'Метрики качества RAG системы из автоматической оценки';
COMMENT ON COLUMN rag_quality_metrics.top_k IS 'Количество контекстов использованных при поиске';
COMMENT ON COLUMN rag_quality_metrics.avg_faithfulness IS 'Средняя верность ответа контексту (0-1)';
COMMENT ON COLUMN rag_quality_metrics.avg_answer_relevance IS 'Средняя релевантность ответа вопросу (0-1)';
COMMENT ON COLUMN rag_quality_metrics.avg_context_precision IS 'Средняя точность выбранных контекстов (0-1)';
COMMENT ON COLUMN rag_quality_metrics.avg_context_recall IS 'Средняя полнота охвата контекста (0-1)';
COMMENT ON COLUMN rag_quality_metrics.total_questions IS 'Количество тестовых вопросов';
COMMENT ON COLUMN rag_quality_metrics.avg_evaluation_time IS 'Среднее время оценки одного вопроса в секундах';
