"""
Document Table Component - Display documents with pagination and actions
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi


def show_document_table(api: RAGApi, category: str = 'Все', search: str = ''):
    """Display documents in a table with actions"""
    
    # Pagination
    if 'doc_page' not in st.session_state:
        st.session_state.doc_page = 1
    
    page_size = 20
    
    # Fetch documents
    result = api.get_documents(
        page=st.session_state.doc_page,
        page_size=page_size,
        category=category,
        search=search
    )
    
    docs = result['documents']
    total = result['total']
    total_pages = result['total_pages']
    
    # Display info
    st.write(f"📊 Показано **{len(docs)}** из **{total}** документов")
    
    if not docs:
        st.info("Документы не найдены. Попробуйте изменить фильтры или добавить новый документ.")
        return
    
    # Display documents
    for doc in docs:
        doc_id = doc['id']
        metadata = doc.get('metadata', {})
        category = metadata.get('category', 'N/A')
        doc_type = metadata.get('type', 'N/A')
        
        # Create expander with document preview
        content_preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
        
        # Convert doc_id to string if it's an integer
        doc_id_str = str(doc_id)
        
        with st.expander(f"📄 {doc_id_str[:8]}... | Категория: **{category}** | Тип: {doc_type}"):
            # Content
            st.markdown("**Содержимое:**")
            st.text_area(
                "Полное содержимое",
                value=doc['content'],
                height=150,
                disabled=True,
                key=f"content_{doc_id}",
                label_visibility="collapsed"
            )
            
            # Metadata
            st.markdown("**Метаданные:**")
            st.json(metadata)
            
            # Created date
            created_at = doc.get('created_at', 'N/A')
            st.caption(f"📅 Создано: {created_at}")
            
            # Actions
            st.divider()
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✏️ Редактировать", key=f"edit_{doc_id}", use_container_width=True):
                    st.session_state.edit_doc_id = doc_id
                    st.session_state.edit_doc_content = doc['content']
                    st.session_state.edit_doc_metadata = metadata.copy()
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Удалить", key=f"delete_{doc_id}", use_container_width=True):
                    # Show confirmation
                    st.session_state.delete_confirm_id = doc_id
            
            with col3:
                # Quality indicators
                keywords_count = len(metadata.get('keywords', []))
                st.caption(f"🔑 Ключевые слова: {keywords_count}")
    
    # Handle delete confirmation
    if 'delete_confirm_id' in st.session_state:
        st.warning(f"⚠️ Подтвердите удаление документа {st.session_state.delete_confirm_id[:8]}...?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Да, удалить", type="primary", key="confirm_delete_yes"):
                result = api.delete_document(st.session_state.delete_confirm_id)
                if result['success']:
                    st.success("✅ Документ успешно удален!")
                    del st.session_state.delete_confirm_id
                    st.rerun()
                else:
                    st.error(f"❌ Ошибка: {result['error']}")
        
        with col2:
            if st.button("❌ Отмена", key="confirm_delete_no"):
                del st.session_state.delete_confirm_id
                st.rerun()
    
    # Pagination controls
    if total_pages > 1:
        st.divider()
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            if st.session_state.doc_page > 1:
                if st.button("⬅️ Предыдущая", key="prev_page"):
                    st.session_state.doc_page -= 1
                    st.rerun()
            else:
                st.button("⬅️ Предыдущая", disabled=True, key="prev_page_disabled")
        
        with col2:
            st.write(f"**Страница {st.session_state.doc_page}** из {total_pages}")
        
        with col3:
            # Page selector
            selected_page = st.selectbox(
                "Перейти на страницу:",
                range(1, total_pages + 1),
                index=st.session_state.doc_page - 1,
                key="page_selector",
                label_visibility="collapsed"
            )
            if selected_page != st.session_state.doc_page:
                st.session_state.doc_page = selected_page
                st.rerun()
        
        with col4:
            if st.session_state.doc_page < total_pages:
                if st.button("Следующая ➡️", key="next_page"):
                    st.session_state.doc_page += 1
                    st.rerun()
            else:
                st.button("Следующая ➡️", disabled=True, key="next_page_disabled")
