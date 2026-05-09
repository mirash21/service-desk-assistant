"""
Analytics Page - Basic statistics and monitoring
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi

st.set_page_config(page_title="Аналитика - Admin Panel", layout="wide")

# Title
st.title("📊 Аналитика и мониторинг")

# Initialize API
api = RAGApi()

# KPI Cards
st.subheader("📈 Ключевые метрики")

col1, col2, col3, col4 = st.columns(4)

# Total documents
result = api.get_documents(page=1, page_size=1)
total_docs = result['total']
col1.metric("Всего документов", total_docs)

# Categories count
categories = api.get_categories()
col2.metric("Категорий", len(categories))

# Documents with keywords (sample check)
sample_result = api.get_documents(page=1, page_size=100)
docs_with_keywords = sum(
    1 for doc in sample_result['documents'] 
    if doc.get('metadata', {}).get('keywords')
)
keywords_pct = (docs_with_keywords / len(sample_result['documents']) * 100) if sample_result['documents'] else 0
col3.metric("С ключевыми словами", f"{keywords_pct:.0f}%")

# Documents with category
docs_with_category = sum(
    1 for doc in sample_result['documents'] 
    if doc.get('metadata', {}).get('category') and doc['metadata']['category'] != 'unknown'
)
category_pct = (docs_with_category / len(sample_result['documents']) * 100) if sample_result['documents'] else 0
col4.metric("С категорией", f"{category_pct:.0f}%")

st.divider()

# Unanswered Questions Section
st.subheader("❓ Невозвращенные вопросы")

unanswered_file = 'data/unanswered_questions.json'

if os.path.exists(unanswered_file):
    try:
        with open(unanswered_file, 'r', encoding='utf-8') as f:
            unanswered_data = json.load(f)
        
        if isinstance(unanswered_data, list):
            total_unanswered = len(unanswered_data)
            st.metric("Всего невозвращенных", total_unanswered)
            
            if total_unanswered > 0:
                # Show recent unanswered questions
                st.write("**Последние невозвращенные вопросы:**")
                
                # Display last 10 questions
                recent_questions = unanswered_data[-10:] if len(unanswered_data) > 10 else unanswered_data
                
                for i, qa in enumerate(reversed(recent_questions)):
                    question = qa.get('question', 'N/A') if isinstance(qa, dict) else str(qa)
                    timestamp = qa.get('timestamp', 'N/A') if isinstance(qa, dict) else 'N/A'
                    
                    with st.expander(f"Q{i+1}: {question[:100]}..."):
                        st.write(f"**Вопрос:** {question}")
                        st.write(f"**Время:** {timestamp}")
                        
                        if isinstance(qa, dict) and 'suggested_answer' in qa:
                            st.write(f"**Предложенный ответ:** {qa['suggested_answer']}")
        else:
            st.info("Нет данных о невозвращенных вопросах")
    
    except Exception as e:
        st.error(f"Ошибка загрузки невозвращенных вопросов: {e}")
else:
    st.info(f"Файл не найден: {unanswered_file}")
    st.caption("Невозвращенные вопросы появятся здесь, когда пользователи задают вопросы, на которые бот не может ответить.")

st.divider()

# Quality Analysis
st.subheader("✅ Анализ качества")

# Analyze sample of documents
if sample_result['documents']:
    quality_metrics = {
        'avg_length': 0,
        'short_chunks': 0,
        'long_chunks': 0,
        'optimal_chunks': 0
    }
    
    lengths = [len(doc['content']) for doc in sample_result['documents']]
    quality_metrics['avg_length'] = sum(lengths) / len(lengths) if lengths else 0
    
    for length in lengths:
        if length < 200:
            quality_metrics['short_chunks'] += 1
        elif length > 600:
            quality_metrics['long_chunks'] += 1
        else:
            quality_metrics['optimal_chunks'] += 1
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Средняя длина чанка", f"{quality_metrics['avg_length']:.0f} симв.")
    col2.metric("Оптимальные чанки", f"{quality_metrics['optimal_chunks']} ({quality_metrics['optimal_chunks']/len(sample_result['documents'])*100:.0f}%)")
    col3.metric("Требуют оптимизации", f"{quality_metrics['short_chunks'] + quality_metrics['long_chunks']}")
    
    # Recommendations
    st.write("**Рекомендации:**")
    
    if quality_metrics['long_chunks'] > 0:
        st.warning(f"- {quality_metrics['long_chunks']} чанков слишком длинные (>600 симв.). Рассмотрите возможность их разделения.")
    
    if quality_metrics['short_chunks'] > 0:
        st.info(f"- {quality_metrics['short_chunks']} чанков короткие (<200 симв.). Рассмотрите возможность их объединения или расширения.")
    
    if keywords_pct < 80:
        st.warning(f"- Только {keywords_pct:.0f}% документов имеют ключевые слова. Используйте автоисправление при добавлении новых документов.")
    
    if category_pct < 80:
        st.warning(f"- Только {category_pct:.0f}% документов имеют категории. Убедитесь что категория установлена при добавлении документов.")

st.divider()

# Export Section
st.subheader("📥 Экспорт данных")

col1, col2 = st.columns(2)

with col1:
    if st.button("Экспорт информации о документах", use_container_width=True):
        # Create export data
        export_data = []
        for doc in sample_result['documents']:
            export_data.append({
                'id': doc['id'],
                'category': doc.get('metadata', {}).get('category', 'N/A'),
                'content_length': len(doc['content']),
                'has_keywords': bool(doc.get('metadata', {}).get('keywords')),
                'created_at': doc.get('created_at', 'N/A')
            })
        
        # Show as JSON
        st.json(export_data[:5])  # Show first 5
        st.caption("Показан образец. Полная функция экспорта скоро будет доступна.")

with col2:
    if st.button("Экспорт невозвращенных вопросов", use_container_width=True):
        if os.path.exists(unanswered_file):
            st.download_button(
                label="Скачать JSON",
                data=json.dumps(unanswered_data, ensure_ascii=False, indent=2),
                file_name=f"unanswered_questions_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        else:
            st.info("Нет данных для экспорта")

st.divider()

st.caption("💡 Совет: Регулярный мониторинг помогает поддерживать высокое качество базы знаний")
