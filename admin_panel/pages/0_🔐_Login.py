"""
Login Page - Аутентификация администратора
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Вход - Admin Panel",
    page_icon="🔐",
    layout="centered"
)

def validate_credentials(username: str, password: str) -> bool:
    """Validate credentials against environment variables"""
    admin_user = os.getenv('ADMIN_USERNAME')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    
    # Если переменные не установлены, вход запрещен
    if not admin_user or not admin_pass:
        return False
    
    return username == admin_user and password == admin_pass

# Форма входа
st.title("🔐 Вход в систему")
st.write("Введите учетные данные для доступа к панели администратора")

with st.form("login_form"):
    username = st.text_input(
        "Имя пользователя",
        placeholder="Введите имя пользователя"
    )
    password = st.text_input(
        "Пароль",
        type="password",
        placeholder="Введите пароль"
    )
    
    submitted = st.form_submit_button("🚀 Войти", use_container_width=True, type="primary")
    
    if submitted:
        if not username or not password:
            st.error("❌ Пожалуйста, введите имя пользователя и пароль")
        elif validate_credentials(username, password):
            # Успешный вход
            st.session_state.authenticated = True
            st.session_state.username = username
            
            st.success("✅ Вход выполнен успешно! Перенаправление...")
            st.balloons()
            
            # Перенаправление на главную страницу
            st.switch_page("app.py")
        else:
            st.error("❌ Неверное имя пользователя или пароль")
