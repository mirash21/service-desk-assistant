"""
Documents Management Page - Browse, add, edit, delete documents
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi
from components.document_table import show_document_table
from components.document_editor import show_add_document_form, show_edit_document_form

st.set_page_config(page_title="Документы - Admin Panel", layout="wide")

# Initialize session state
if 'filter_category' not in st.session_state:
    st.session_state.filter_category = 'Все'
if 'filter_search' not in st.session_state:
    st.session_state.filter_search = ''
if 'doc_page' not in st.session_state:
    st.session_state.doc_page = 1
if 'edit_doc_id' not in st.session_state:
    st.session_state.edit_doc_id = None
if 'edit_doc_content' not in st.session_state:
    st.session_state.edit_doc_content = ''
if 'edit_doc_metadata' not in st.session_state:
    st.session_state.edit_doc_metadata = {}

# Initialize API
api = RAGApi()

# Title
st.title("📚 Управление базой знаний")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Фильтры")
    
    # Get available categories
    categories = api.get_categories()
    category_options = ['Все'] + categories
    
    # Category filter
    selected_category = st.selectbox(
        "Категория",
        category_options,
        index=category_options.index(st.session_state.filter_category) if st.session_state.filter_category in category_options else 0
    )
    
    # Search filter
    search_query = st.text_input(
        "Поиск по содержимому",
        value=st.session_state.filter_search,
        placeholder="Введите текст для поиска..."
    )
    
    # Apply filters button
    if st.button("Применить фильтры", use_container_width=True):
        st.session_state.filter_category = selected_category
        st.session_state.filter_search = search_query
        st.session_state.doc_page = 1  # Reset to first page
        st.rerun()
    
    # Clear filters
    if st.button("Очистить фильтры", use_container_width=True):
        st.session_state.filter_category = 'Все'
        st.session_state.filter_search = ''
        st.session_state.doc_page = 1
        st.rerun()
    
    st.divider()
    
    # Quick stats
    st.subheader("📊 Быстрая статистика")
    
    # Get total count
    result = api.get_documents(page=1, page_size=1)
    total_docs = result['total']
    
    st.metric("Всего документов", total_docs)
    
    if selected_category != 'Все':
        st.caption(f"Фильтр по категории: {selected_category}")
    if search_query:
        st.caption(f"Поиск: '{search_query}'")

# Main content - Tabs
tab1, tab2 = st.tabs(["📋 Просмотр документов", "➕ Добавить новый документ"])

with tab1:
    # Check if we're in edit mode
    if st.session_state.get('edit_doc_id') is not None:
        # Show edit form
        show_edit_document_form(
            st.session_state.edit_doc_id,
            st.session_state.edit_doc_content,
            st.session_state.edit_doc_metadata
        )
        
        # Back button
        if st.button("⬅️ Назад к списку"):
            del st.session_state.edit_doc_id
            del st.session_state.edit_doc_content
            del st.session_state.edit_doc_metadata
            st.rerun()
    else:
        # Show document table
        show_document_table(
            api,
            category=st.session_state.filter_category,
            search=st.session_state.filter_search
        )

with tab2:
    # Show add form
    show_add_document_form()
