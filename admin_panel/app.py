"""
Service Desk Assistant - Admin Panel
Главное приложение Streamlit
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Service Desk Admin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_custom_css():
    """Load custom styles"""
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .success-box {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 1rem;
            margin: 1rem 0;
        }
        .warning-box {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-box {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'filter_category' not in st.session_state:
        st.session_state.filter_category = 'Все'
    if 'filter_search' not in st.session_state:
        st.session_state.filter_search = ''
    if 'page' not in st.session_state:
        st.session_state.page = 1

# Load custom styles
load_custom_css()

# Initialize session
initialize_session()

# Check authentication
if not st.session_state.get('authenticated', False):
    # Redirect to login page
    st.switch_page("pages/0_🔐_Login.py")
else:
    # Main application
    with st.sidebar:
        st.title("🤖 Панель администратора")
        st.write(f"**Добро пожаловать,** {st.session_state.get('username', 'Админ')}!")
        st.divider()
        
        # Navigation info
        st.info("📌 Используйте страницы в боковой панели для навигации")
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
    
    # Main content
    st.markdown('<h1 class="main-header">Service Desk Assistant - Панель администратора</h1>', unsafe_allow_html=True)
    
    st.success("✅ Добро пожаловать в панель администратора! Выберите страницу из боковой панели чтобы начать.")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Статус", "🟢 Онлайн")
    
    with col2:
        st.metric("База данных", "🟢 Подключена")
    
    with col3:
        st.metric("Версия", "v1.0.0")
    
    st.divider()
    
    # Features overview
    st.subheader("🎯 Доступные функции")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.markdown("""
        **📚 Управление базой знаний**
        - Просмотр всех документов
        - Добавление новых Q&A пар
        - Редактирование существующих документов
        - Удаление документов
        - Проверка качества
        """)
    
    with feature_col2:
        st.markdown("""
        **📊 Аналитика и мониторинг**
        - Статистика использования
        - Невозвращенные вопросы
        - Метрики качества
        - Экспорт данных
        """)
    
    st.divider()
    
    # New Activities section
    st.subheader("💬 История диалогов")
    
    activities_col1, activities_col2 = st.columns(2)
    
    with activities_col1:
        st.markdown("""
        **👥 Мониторинг пользователей**
        - Просмотр истории чатов по пользователям
        - Фильтрация по периоду
        - Анализ типов сообщений (текст, голос, изображения)
        - Отслеживание активности
        """)
    
    with activities_col2:
        st.markdown("""
        **🔍 Детальный анализ**
        - Просмотр полных диалогов
        - Метаданные сообщений
        - Статистика по пользователям
        - Поиск по содержимому
        """)
    
    st.divider()
    
    st.caption("💡 Совет: Начните со страницы 'Документы' для управления базой знаний")
