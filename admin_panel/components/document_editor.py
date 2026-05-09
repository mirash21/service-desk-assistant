"""
Document Editor Component - Add and Edit document forms
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi
from components.quality_indicator import show_validation_result


def show_add_document_form():
    """Form for adding new document"""
    
    st.header("➕ Добавить новый документ")
    
    api = RAGApi()
    
    with st.form("add_document_form", clear_on_submit=True):
        # Category selection
        category = st.selectbox(
            "Категория",
            ["printers", "network", "email", "password", 
             "software", "hardware", "security", "windows", "office", "crm", "mobile", "general"],
            index=11  # Default to 'general'
        )
        
        # Question
        question = st.text_area(
            "❓ Вопрос (В: ...)",
            placeholder="В: Как подключить принтер?",
            height=100,
            help="Введите вопрос пользователя на естественном языке"
        )
        
        # Answer
        answer = st.text_area(
            "💡 Ответ (О: ...)",
            placeholder="О: Подключите через USB кабель. Установите драйверы с сайта производителя.",
            height=200,
            help="Предоставьте четкий пошаговый ответ"
        )
        
        # Auto-fix option
        auto_fix = st.checkbox(
            "🔧 Включить автоисправление (рекомендуется)", 
            value=True,
            help="Автоматически добавляет ключевые слова, определяет категорию и предлагает синонимы"
        )
        
        # Preview validation button
        col_preview, col_submit = st.columns([1, 2])
        
        with col_preview:
            preview_clicked = st.form_submit_button("👁️ Предпросмотр проверки")
        
        # Show validation if preview clicked
        if preview_clicked:
            if question and answer:
                content = f"В: {question}\nО: {answer}"
                metadata = {'category': category, 'type': 'faq', 'format': 'qa'}
                
                validation = api.validate_document(content, metadata)
                show_validation_result(validation)
            else:
                st.warning("⚠️ Пожалуйста, сначала заполните вопрос и ответ")
        
        # Submit button
        with col_submit:
            submitted = st.form_submit_button("💾 Сохранить документ", type="primary", use_container_width=True)
        
        if submitted:
            if not question or not answer:
                st.error("❌ Пожалуйста, заполните вопрос и ответ")
            else:
                # Format content
                content = f"В: {question}\nО: {answer}"
                metadata = {
                    'category': category,
                    'type': 'faq',
                    'format': 'qa'
                }
                
                # Add document
                with st.spinner("Сохранение документа..."):
                    result = api.add_document(
                        content=content,
                        metadata=metadata,
                        auto_fix=auto_fix
                    )
                
                if result['success']:
                    st.success(f"✅ Документ успешно добавлен! ID: {result.get('document_id', 'N/A')[:8]}...")
                    st.balloons()
                    
                    # Show metadata that was added
                    if 'metadata' in result:
                        st.json(result['metadata'])
                else:
                    st.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")


def show_edit_document_form(doc_id: str, content: str, metadata: dict):
    """Form for editing existing document"""
    
    if not doc_id:
        st.error("❌ Документ не выбран для редактирования")
        return
    
    st.header(f"✏️ Редактирование документа {doc_id[:8]}...")
    
    api = RAGApi()
    
    # Parse Q&A format
    lines = content.split('\n')
    question = ""
    answer = ""
    
    for line in lines:
        if line.startswith('В:') or line.startswith('Q:'):
            question = line[2:].strip()
        elif line.startswith('О:') or line.startswith('A:'):
            answer = line[2:].strip()
        elif answer:
            answer += "\n" + line
    
    with st.form("edit_document_form"):
        # Category selection
        categories = ["printers", "network", "email", "password", 
                     "software", "hardware", "security", "windows", "office", "crm", "mobile", "general"]
        
        current_category = metadata.get('category', 'general')
        default_index = categories.index(current_category) if current_category in categories else 11
        
        category = st.selectbox(
            "Категория",
            categories,
            index=default_index
        )
        
        # Question and Answer
        question = st.text_area("❓ Вопрос", value=question, height=100)
        answer = st.text_area("💡 Ответ", value=answer, height=200)
        
        # Buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("💾 Обновить", type="primary", use_container_width=True)
        
        with col2:
            cancel = st.form_submit_button("❌ Отмена", use_container_width=True)
        
        if submitted:
            if not question or not answer:
                st.error("❌ Пожалуйста, заполните вопрос и ответ")
            else:
                # Format content
                content = f"В: {question}\nО: {answer}"
                metadata['category'] = category
                
                # Update document
                with st.spinner("Обновление документа..."):
                    result = api.update_document(doc_id, content, metadata)
                
                if result['success']:
                    st.success("✅ Документ успешно обновлен!")
                    
                    # Clear edit state
                    if 'edit_doc_id' in st.session_state:
                        del st.session_state.edit_doc_id
                    if 'edit_doc_content' in st.session_state:
                        del st.session_state.edit_doc_content
                    if 'edit_doc_metadata' in st.session_state:
                        del st.session_state.edit_doc_metadata
                    
                    st.rerun()
                else:
                    st.error(f"❌ Ошибка: {result['error']}")
        
        if cancel:
            # Clear edit state
            if 'edit_doc_id' in st.session_state:
                del st.session_state.edit_doc_id
            if 'edit_doc_content' in st.session_state:
                del st.session_state.edit_doc_content
            if 'edit_doc_metadata' in st.session_state:
                del st.session_state.edit_doc_metadata
            
            st.rerun()
