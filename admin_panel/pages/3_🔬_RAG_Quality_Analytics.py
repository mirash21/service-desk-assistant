"""
RAG Quality Analytics Page - Визуализация метрик качества RAG системы
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import requests
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi

st.set_page_config(page_title="RAG Quality Analytics - Admin Panel", layout="wide")

# Title
st.title("📊 Аналитика качества RAG системы")
st.caption("Автоматическая оценка с использованием метрик RAGAS")

# Initialize API
api = RAGApi()

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Текущие результаты", "🔄 Запустить оценку", "📚 Документация"])

with tab1:
    st.subheader("📈 Сравнение результатов для разных top_k")
    
    # Fetch latest results from Supabase
    try:
        result = api.supabase.table('rag_quality_metrics').select('*').order(
            'evaluated_at', desc=True
        ).limit(10).execute()
        
        if not result.data:
            st.warning("⚠️ Нет данных в базе. Запустите оценку на вкладке '🔄 Запустить оценку'")
            st.stop()
        
        # Convert to DataFrame
        df = pd.DataFrame(result.data)
        
        # Debug info
        with st.expander("🔍 Отладочная информация"):
            st.write(f"Всего записей: {len(df)}")
            st.write(f"Колонки: {list(df.columns)}")
            st.dataframe(df.head(), use_container_width=True)
        
        # Get unique evaluation runs
        eval_dates = df['evaluated_at'].unique()
        
        if len(eval_dates) > 0:
            # Show latest evaluation
            latest_date = eval_dates[0]
            latest_df = df[df['evaluated_at'] == latest_date].sort_values('top_k')
            
            st.write(f"**Последняя оценка:** {latest_date}")
            
            # Display comparison table
            col1, col2, col3, col4 = st.columns(4)
            
            for _, row in latest_df.iterrows():
                with st.expander(f"Top-K = {int(row['top_k'])}"):
                    st.metric("Faithfulness", f"{row['avg_faithfulness']:.3f}")
                    st.metric("Answer Relevance", f"{row['avg_answer_relevance']:.3f}")
                    st.metric("Context Precision", f"{row['avg_context_precision']:.3f}")
                    st.metric("Context Recall", f"{row['avg_context_recall']:.3f}")
                    st.caption(f"Вопросов: {int(row['total_questions'])}, Время: {row['avg_evaluation_time']:.2f}s")
            
            # Chart: Metrics comparison
            st.write("\n**График сравнения метрик:**")
            
            # Prepare data for chart
            chart_data = latest_df[['top_k', 'avg_faithfulness', 'avg_answer_relevance', 
                                   'avg_context_precision', 'avg_context_recall']].copy()
            chart_data = chart_data.set_index('top_k')
            chart_data.columns = ['Faithfulness', 'Answer Relevance', 
                                 'Context Precision', 'Context Recall']
            
            # Display line chart
            st.line_chart(chart_data)
            
            # Recommendation
            best_row = latest_df.loc[
                (latest_df['avg_faithfulness'] + 
                 latest_df['avg_answer_relevance'] + 
                 latest_df['avg_context_precision'] + 
                 latest_df['avg_context_recall']).idxmax()
            ]
            
            st.success(f"""
            💡 **Рекомендация:** Оптимальное значение top_k = {int(best_row['top_k'])}
            
            Средний composite score: {(best_row['avg_faithfulness'] + best_row['avg_answer_relevance'] + best_row['avg_context_precision'] + best_row['avg_context_recall']) / 4:.3f}
            """)
            
            # Historical trend
            if len(eval_dates) > 1:
                st.write("\n**История оценок:**")
                
                history_df = df.groupby(['evaluated_at', 'top_k']).agg({
                    'avg_faithfulness': 'mean',
                    'avg_answer_relevance': 'mean',
                    'avg_context_precision': 'mean',
                    'avg_context_recall': 'mean'
                }).reset_index()
                
                st.dataframe(history_df, use_container_width=True)
        else:
            st.info("Нет данных об оценках. Запустите оценку на вкладке 'Запустить оценку'.")
    
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        st.caption("Убедитесь что таблица rag_quality_metrics создана в Supabase")

with tab2:
    st.subheader("🔄 Запуск новой оценки качества")
    
    st.write("""
    Этот инструмент запустит автоматическую оценку качества RAG системы:
    
    1. Сгенерирует тестовые вопросы из базы знаний
    2. Запустит оценку с разными значениями top_k (3, 5, 10)
    3. Рассчитает метрики RAGAS (Faithfulness, Answer Relevance, Context Precision, Context Recall)
    4. Сохранит результаты для анализа
    
    ⚠️ **Внимание:** Оценка может занять несколько минут в зависимости от количества вопросов.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sample_size = st.number_input(
            "Количество тестовых вопросов",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Больше вопросов = точнее оценка, но дольше выполнение"
        )
    
    with col2:
        top_k_values = st.text_input(
            "Значения top_k для тестирования",
            value="3,5,10",
            help="Через запятую, например: 3,5,10"
        )
    
    st.subheader("🔄 Запуск оценки качества RAG")
    
    st.info("""
    🚀 **Автоматический запуск оценки**
    
    Нажмите кнопку ниже для запуска автоматической оценки качества RAG системы.
    Процесс выполняется в фоновом режиме и занимает 5-10 минут.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sample_size = st.number_input(
            "Количество тестовых вопросов",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="Рекомендуется 30-50 вопросов"
        )
    
    with col2:
        top_k_values = st.text_input(
            "Значения top_k для сравнения",
            value="3,5,10",
            help="Через запятую, например: 3,5,10"
        )
    
    # API endpoint
    api_url = os.getenv('RAG_ANALYTICS_API_URL', 'http://max-bot-webhook:8766')
    
    if st.button("🚀 Запустить оценку", type="primary", use_container_width=True):
        try:
            # Отправляем запрос на API
            with st.spinner('Отправка запроса на запуск оценки...'):
                response = requests.post(
                    f'{api_url}/run-evaluation',
                    json={
                        'sample_size': sample_size,
                        'top_k': top_k_values
                    },
                    timeout=10
                )
            
            if response.status_code == 202:
                st.success("✅ Оценка запущена в фоновом режиме!")
                
                result = response.json()
                st.info(f"""
                **Статус:** {result['message']}
                
                **Параметры:**
                - Количество вопросов: {result['parameters']['sample_size']}
                - Top-K значения: {result['parameters']['top_k']}
                
                ⏱️ **Ожидаемое время выполнения:** 5-10 минут
                
                💡 После завершения оценки обновите эту страницу чтобы увидеть результаты на вкладке "📈 Текущие результаты".
                """)
                
                # Progress simulation
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(100):
                    time.sleep(3)  # Check every 3 seconds
                    progress_bar.progress(i + 1)
                    
                    if i < 20:
                        status_text.text("⏳ Генерация тестовых вопросов...")
                    elif i < 40:
                        status_text.text("⏳ Поиск релевантных документов...")
                    elif i < 60:
                        status_text.text("⏳ Генерация ответов через LLM...")
                    elif i < 80:
                        status_text.text("⏳ Расчет метрик RAGAS...")
                    else:
                        status_text.text("⏳ Сохранение результатов...")
                
                progress_bar.progress(100)
                status_text.text("✅ Проверьте логи контейнера max-bot-webhook для деталей")
                
                st.balloons()
                
            else:
                st.error(f"❌ Ошибка запуска: HTTP {response.status_code}")
                st.error(response.text)
        
        except requests.exceptions.ConnectionError:
            st.error("""
            ❌ Не удалось подключиться к API серверу аналитики.
            
            **Возможные причины:**
            1. API сервер не запущен в контейнере max-bot-webhook
            2. Неправильный URL: проверьте переменную окружения RAG_ANALYTICS_API_URL
            
            **Решение:**
            Запустите API сервер:
            ```bash
            docker exec -d max-bot-webhook python3 /app/scripts/rag_analytics_api.py
            ```
            """)
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
    
    st.markdown("---")
    
    st.write("**Что происходит при нажатии кнопки:**")
    st.write("1. ✅ Admin Panel отправляет запрос на API сервер (порт 8765)")
    st.write("2. ✅ API сервер запускает скрипт rag_quality_analytics.py в фоне")
    st.write(f"3. ✅ Скрипт генерирует {sample_size} тестовых вопросов из базы знаний")
    st.write(f"4. ✅ Запускается оценка с top_k = {top_k_values}")
    st.write("5. ✅ Рассчитываются метрики RAGAS (Faithfulness, Relevance, Precision, Recall)")
    st.write("6. ✅ Результаты сохраняются в Supabase")
    st.write("7. ✅ Обновите страницу чтобы увидеть новые результаты")
    
    st.warning("⏱️ Время выполнения: ~5-10 минут в зависимости от количества вопросов")

with tab3:
    st.subheader("📚 Документация по метрикам RAGAS")
    
    st.markdown("""
    ## Метрики качества RAG системы
    
    ### 1. Faithfulness (Верность контексту)
    **Что измеряет:** Насколько ответ основан на предоставленных контекстах
    
    **Диапазон:** 0-1 (выше = лучше)
    
    **Интерпретация:**
    - 0.9-1.0: Отлично - ответ полностью основан на контексте
    - 0.7-0.9: Хорошо - ответ в основном соответствует контексту
    - <0.7: Требует улучшения - возможны галлюцинации
    
    ---
    
    ### 2. Answer Relevance (Релевантность ответа)
    **Что измеряет:** Насколько ответ релевантен заданному вопросу
    
    **Диапазон:** 0-1 (выше = лучше)
    
    **Интерпретация:**
    - 0.9-1.0: Отлично - ответ точно отвечает на вопрос
    - 0.7-0.9: Хорошо - ответ в целом релевантен
    - <0.7: Требует улучшения - ответ может быть не по теме
    
    ---
    
    ### 3. Context Precision (Точность контекста)
    **Что измеряет:** Насколько выбранные контексты релевантны вопросу
    
    **Диапазон:** 0-1 (выше = лучше)
    
    **Интерпретация:**
    - 0.9-1.0: Отлично - все контексты релевантны
    - 0.7-0.9: Хорошо - большинство контекстов полезны
    - <0.7: Требует улучшения - много нерелевантных контекстов
    
    ---
    
    ### 4. Context Recall (Полнота контекста)
    **Что измеряет:** Какая часть необходимой информации найдена в контекстах
    
    **Диапазон:** 0-1 (выше = лучше)
    
    **Интерпретация:**
    - 0.9-1.0: Отлично - вся необходимая информация найдена
    - 0.7-0.9: Хорошо - большая часть информации найдена
    - <0.7: Требует улучшения - важная информация отсутствует
    
    ---
    
    ## Параметр Top-K
    
    **Что это:** Количество документов/чанков которые RAG система извлекает для генерации ответа
    
    **Trade-offs:**
    - **Маленький top_k (3):** Быстрее, меньше шума, но может пропустить важную информацию
    - **Средний top_k (5):** Баланс между точностью и полнотой
    - **Большой top_k (10+):** Больше информации, но больше шума и медленнее
    
    **Как выбрать оптимальное значение:**
    1. Запустите оценку с разными значениями top_k
    2. Сравните средние значения всех 4 метрик
    3. Выберите top_k с наилучшим composite score
    4. Учитывайте время ответа (avg_evaluation_time)
    
    ---
    
    ## Автоматизация
    
    ### Запуск через командную строку:
    ```bash
    # Базовый запуск
    python3 scripts/rag_quality_analytics.py
    
    # С кастомными параметрами
    python3 scripts/rag_quality_analytics.py --sample 100 --top-k 3,5,10,15
    
    # Через Docker
    docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py
    ```
    
    ### Настройка cron для регулярной оценки:
    ```bash
    # Еженедельная оценка (каждое воскресенье в 2:00)
    0 2 * * 0 cd /home/mirash/service-desk-assistant && \
      docker exec max-bot-webhook python3 /app/scripts/rag_quality_analytics.py \
      >> logs/rag_quality.log 2>&1
    ```
    
    ---
    
    ## Установка зависимостей
    
    Для использования полноценных метрик RAGAS установите:
    ```bash
    pip install ragas langchain-openai langchain-community datasets
    ```
    
    Без RAGAS будет использоваться fallback режим с базовыми эвристиками.
    
    ---
    
    ## Интерпретация результатов
    
    ### Хорошие показатели:
    - Все метрики > 0.8
    - Минимальная разница между разными top_k
    - Стабильные результаты во времени
    
    ### Требуется внимание:
    - Любая метрика < 0.6
    - Большая вариативность между top_k
    - Ухудшение показателей со временем
    
    ### Действия при низких показателях:
    1. **Низкий Faithfulness:** Проверьте качество чанков, возможно есть противоречия
    2. **Низкий Answer Relevance:** Улучшите prompt engineering или модель
    3. **Низкий Context Precision:** Оптимизируйте embeddings или стратегию поиска
    4. **Низкий Context Recall:** Увеличьте размер базы знаний или улучшите chunking
    """)
    
    st.divider()
    
    st.caption("💡 Совет: Регулярно запускайте оценку (еженедельно) для мониторинга качества RAG системы")
