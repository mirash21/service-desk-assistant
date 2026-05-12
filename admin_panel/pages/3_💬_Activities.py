"""
Activities Page - Chat history organized by users
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_api import RAGApi

st.set_page_config(page_title="Деятельность - Admin Panel", layout="wide")

# Title
st.title("💬 Деятельность (История чатов)")

# Initialize API
api = RAGApi()

# Cache functions for better performance
@st.cache_data(ttl=60)  # Кэш на 60 секунд
def get_cached_unique_users():
    """Кэшированный список пользователей"""
    return api.get_unique_users()

@st.cache_data(ttl=60)  # Кэш на 60 секунд
def get_cached_user_stats():
    """Кэшированная статистика пользователей"""
    return api.get_user_stats()

@st.cache_data(ttl=30)  # Кэш на 30 секунд для истории
def get_cached_chat_history(user_id=None, page=1, page_size=50):
    """Кэшированная история чата"""
    return api.get_chat_history(user_id=user_id, page=page, page_size=page_size)

# Sidebar - User Selection
with st.sidebar:
    st.header("👥 Фильтры")
    
    # Get unique users with caching
    with st.spinner("Загрузка списка пользователей..."):
        unique_users = get_cached_unique_users()
    
    if not unique_users:
        st.info("Нет данных об активности пользователей")
        st.stop()
    
    # User selector
    selected_user = st.selectbox(
        "Выберите пользователя:",
        options=["Все пользователи"] + unique_users,
        index=0
    )
    
    # Date range filter
    st.divider()
    st.subheader("📅 Период")
    
    date_option = st.radio(
        "Период отображения:",
        ["За всё время", "Сегодня", "Последние 7 дней", "Последние 30 дней"],
        index=0
    )
    
    # Message type filter
    st.divider()
    message_type_filter = st.multiselect(
        "Тип сообщений:",
        options=["user", "bot"],
        default=["user", "bot"],
        format_func=lambda x: "От пользователя" if x == "user" else "Ответ бота"
    )

# Main content area
if selected_user == "Все пользователи":
    # Show overview with all users
    st.subheader("📊 Общая статистика")
    
    # Get cached stats
    with st.spinner("Загрузка статистики..."):
        user_stats = get_cached_user_stats()
    
    if user_stats:
        # Display stats in columns
        cols = st.columns(min(len(user_stats), 4))
        
        for idx, (user_id, stats) in enumerate(list(user_stats.items())[:len(cols)]):
            with cols[idx % len(cols)]:
                st.metric(
                    f"Пользователь {user_id[:8]}...",
                    f"{stats['total']} сообщ.",
                    delta=f"👤 {stats['user_messages']} | 🤖 {stats['bot_messages']}"
                )
        
        if len(user_stats) > 4:
            st.caption(f"... и ещё {len(user_stats) - 4} пользователей")
    
    st.divider()
    
    # Show recent messages from all users
    st.subheader("🕐 Последние сообщения")
    
    page = st.session_state.get('activities_page', 1)
    page_size = 30
    
    # Get cached chat history
    with st.spinner("Загрузка сообщений..."):
        result = get_cached_chat_history(page=page, page_size=page_size)
    
    if result['messages']:
        for msg in result['messages']:
            # Apply filters
            if message_type_filter and msg['message_type'] not in message_type_filter:
                continue
            
            # Display message
            is_user = msg['message_type'] == 'user'
            
            with st.chat_message("user" if is_user else "assistant"):
                # Header with user ID and timestamp
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{msg['user_id'][:12]}...**")
                
                with col2:
                    created_at = msg.get('created_at', '')
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            st.caption(dt.strftime('%d.%m.%Y %H:%M'))
                        except:
                            st.caption(str(created_at))
                
                with col3:
                    metadata = msg.get('metadata', {})
                    if metadata.get('has_image'):
                        st.caption("🖼️ Изображение")
                    elif metadata.get('has_voice'):
                        st.caption("🎤 Голос")
                    elif metadata.get('command'):
                        st.caption("⚙️ Команда")
                
                # Message content
                st.write(msg['content'])
                
                # Additional metadata info
                if metadata:
                    with st.expander("📋 Метаданные"):
                        st.json(metadata)
        
        # Pagination
        total_pages = result['total_pages']
        if total_pages > 1:
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if page > 1:
                    if st.button("← Назад"):
                        st.session_state.activities_page = page - 1
                        st.rerun()
            
            with col2:
                st.write(f"Страница {page} из {total_pages}")
            
            with col3:
                if page < total_pages:
                    if st.button("Вперёд →"):
                        st.session_state.activities_page = page + 1
                        st.rerun()
    else:
        st.info("Нет сообщений для отображения")

else:
    # Show chat history for specific user
    st.subheader(f"💬 История диалога с пользователем: `{selected_user}`")
    
    # User statistics with caching
    with st.spinner("Загрузка статистики..."):
        user_stats = get_cached_user_stats()
    
    if selected_user in user_stats:
        stats = user_stats[selected_user]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Сообщений от пользователя", stats['user_messages'])
        col2.metric("Ответов бота", stats['bot_messages'])
        col3.metric("Всего сообщений", stats['total'])
    
    st.divider()
    
    # Get chat history for this user with caching
    page = st.session_state.get('activities_page', 1)
    page_size = 50
    
    with st.spinner("Загрузка истории диалога..."):
        result = get_cached_chat_history(user_id=selected_user, page=page, page_size=page_size)
    
    if result['messages']:
        # Group messages by conversation (user message followed by bot response)
        conversations = []
        current_conversation = []
        
        for msg in sorted(result['messages'], key=lambda x: x.get('created_at', '')):
            if msg['message_type'] == 'user':
                if current_conversation:
                    conversations.append(current_conversation)
                current_conversation = [msg]
            else:
                current_conversation.append(msg)
        
        if current_conversation:
            conversations.append(current_conversation)
        
        # Display conversations
        for conv_idx, conversation in enumerate(reversed(conversations)):
            st.markdown("---")
            
            for msg in conversation:
                is_user = msg['message_type'] == 'user'
                
                with st.chat_message("user" if is_user else "assistant"):
                    # Timestamp
                    created_at = msg.get('created_at', '')
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            st.caption(dt.strftime('%d.%m.%Y %H:%M:%S'))
                        except:
                            st.caption(str(created_at))
                    
                    # Content
                    st.write(msg['content'])
                    
                    # Metadata indicators
                    metadata = msg.get('metadata', {})
                    indicators = []
                    
                    if metadata.get('has_image'):
                        indicators.append("🖼️")
                    if metadata.get('has_voice'):
                        indicators.append("🎤")
                    if metadata.get('command'):
                        indicators.append("⚙️")
                    if metadata.get('ticket_created'):
                        indicators.append("🎫")
                    
                    if indicators:
                        st.caption(" ".join(indicators))
        
        # Pagination
        total_pages = result['total_pages']
        if total_pages > 1:
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if page > 1:
                    if st.button("← Назад", key="prev_btn"):
                        st.session_state.activities_page = page - 1
                        st.rerun()
            
            with col2:
                st.write(f"Страница {page} из {total_pages}")
            
            with col3:
                if page < total_pages:
                    if st.button("Вперёд →", key="next_btn"):
                        st.session_state.activities_page = page + 1
                        st.rerun()
    else:
        st.info("Нет сообщений от этого пользователя")

st.divider()
st.caption("💡 Совет: Используйте фильтры в боковой панели для поиска конкретных диалогов")
