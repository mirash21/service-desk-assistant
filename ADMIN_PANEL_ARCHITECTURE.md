# Архитектурное решение: Админ-панель Service Desk Assistant

**Дата:** 27 апреля 2026  
**Версия:** 1.0  
**Статус:** 📋 Proposal

---

## 🎯 Цель

Создать веб-интерфейс "Личный кабинет администратора" для управления ботом технической поддержки с возможностями:
- Управление базой знаний RAG
- Мониторинг и аналитика
- Настройки системы

---

## 🏗️ Архитектурное решение

### Выбор технологического стека

#### ✅ РЕКОМЕНДАЦИЯ: **Streamlit**

**Обоснование выбора:**

| Критерий | Streamlit | React + FastAPI | Gradio | Flask + Jinja2 |
|----------|-----------|-----------------|--------|----------------|
| Скорость разработки | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Интеграция с Python | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Docker совместимость | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Аутентификация | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Масштабируемость | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Learning curve | Низкий | Высокий | Низкий | Средний |
| Поддержка команды | Отличная | Отличная | Хорошая | Отличная |

**Почему Streamlit:**
1. ✅ **Нативная интеграция с Python** - используем существующие утилиты без изменений
2. ✅ **Быстрая разработка** - MVP за 2-3 дня vs 2-3 недели для React
3. ✅ **Встроенная поддержка Docker** - простой deployment
4. ✅ **Аутентификация из коробки** - `streamlit-authenticator` или basic auth
5. ✅ **Идеально для data-driven приложений** - таблицы, графики, фильтры
6. ✅ **Минимальный overhead** - не нужен отдельный frontend team

**Альтернатива (если нужна сложная кастомизация):**
- React + FastAPI backend
- Использовать если требуется mobile app или сложная UX логика

---

## 📐 Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │   Admin Panel     │    │   Main Bot Webhook           │  │
│  │   (Streamlit)     │◄──►│   (FastAPI/Flask)            │  │
│  │   Port: 8501      │    │   Port: 8081                 │  │
│  └────────┬─────────┘    └──────────┬───────────────────┘  │
│           │                         │                       │
│           │                         │                       │
│           ▼                         ▼                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Supabase PostgreSQL (pgvector)               │  │
│  │         - documents table                            │  │
│  │         - embeddings                                 │  │
│  │         - metadata                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │   Shared Utils    │    │   Configuration             │  │
│  │   - validator.py  │    │   - .env                    │  │
│  │   - analyzer.py   │    │   - config.yaml             │  │
│  │   - manager.py    │    └──────────────────────────────┘  │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Структура проекта

```
service-desk-assistant/
│
├── admin_panel/                    # ← НОВАЯ ДИРЕКТОРИЯ
│   ├── __init__.py
│   ├── app.py                      # Главное приложение Streamlit
│   ├── pages/                      # Страницы админ-панели
│   │   ├── 1_📚_База_знаний.py
│   │   ├── 2_📊_Аналитика.py
│   │   ├── 3_⚙️_Настройки.py
│   │   └── 4_🔐_Безопасность.py
│   ├── components/                 # Переиспользуемые компоненты
│   │   ├── document_editor.py
│   │   ├── quality_validator.py
│   │   ├── charts.py
│   │   └── auth.py
│   ├── api/                        # API endpoints для admin panel
│   │   ├── rag_api.py              # CRUD для документов
│   │   ├── analytics_api.py        # Метрики и статистика
│   │   └── config_api.py           # Управление настройками
│   ├── utils/                      # Утилиты специфичные для admin
│   │   ├── auth_manager.py         # Аутентификация
│   │   ├── session_state.py        # Управление состоянием
│   │   └── export_import.py        # Экспорт/импорт данных
│   ├── tests/                      # Тесты admin panel
│   │   ├── test_api.py
│   │   └── test_components.py
│   ├── requirements.txt            # Зависимости admin panel
│   └── Dockerfile                  # Dockerfile для admin panel
│
├── utils/                          # Существующие утилиты (переиспользуем)
│   ├── document_validator.py       # ← Используем напрямую
│   ├── safe_document_manager.py    # ← Используем напрямую
│   ├── rag_quality_analyzer.py     # ← Используем напрямую
│   └── unanswered_analyzer.py      # ← Используем напрямую
│
├── rag/                            # Существующий RAG модуль
│   └── supabase_manager.py         # ← Используем напрямую
│
├── data/                           # Данные
│   ├── unanswered_questions.json   # ← Читаем для аналитики
│   └── exports/                    # Экспорты из admin panel
│
├── docker-compose.yml              # ← Добавляем сервис admin-panel
├── docker-compose.admin.yml        # ← Override для admin panel
└── README_ADMIN.md                 # Документация admin panel
```

---

## 🔌 API Endpoints

### Backend API Layer (FastAPI или Flask Blueprint)

Создадим REST API для взаимодействия admin panel с данными:

#### 1. **RAG Documents API** (`/api/v1/documents`)

```python
# GET /api/v1/documents
# Получить список документов с пагинацией и фильтрацией
Query params:
  - page: int (default=1)
  - page_size: int (default=50)
  - category: str (optional)
  - search: str (optional, поиск по content)
  - min_similarity: float (optional)

Response:
{
  "documents": [
    {
      "id": "uuid",
      "content": "string",
      "metadata": {...},
      "created_at": "timestamp",
      "similarity_score": 0.85
    }
  ],
  "total": 652,
  "page": 1,
  "page_size": 50
}

# POST /api/v1/documents
# Добавить новый документ с валидацией
Body:
{
  "content": "string",
  "metadata": {
    "category": "printers",
    "type": "faq",
    "keywords": ["принтер", "driver"]
  },
  "auto_fix": true  # использовать SafeDocumentManager
}

Response:
{
  "success": true,
  "document_id": "uuid",
  "validation_score": 95,
  "warnings": [...]
}

# PUT /api/v1/documents/{id}
# Обновить существующий документ
Body:
{
  "content": "string",
  "metadata": {...}
}

# DELETE /api/v1/documents/{id}
# Удалить документ

# POST /api/v1/documents/batch
# Пакетное добавление документов
Body:
{
  "documents": [...],
  "auto_fix": true
}

# POST /api/v1/documents/validate
# Предварительная валидация без сохранения
Body:
{
  "content": "string",
  "metadata": {...}
}

Response:
{
  "is_valid": true,
  "score": 85,
  "issues": [],
  "suggestions": [],
  "auto_fixes": {...}
}
```

#### 2. **Analytics API** (`/api/v1/analytics`)

```python
# GET /api/v1/analytics/unanswered-questions
# Получить unanswered questions с фильтрацией
Query params:
  - status: str (pending_review, answered, ignored)
  - date_from: datetime
  - date_to: datetime
  - limit: int (default=100)

Response:
{
  "questions": [
    {
      "question": "string",
      "user_id": "string",
      "timestamp": "datetime",
      "suggested_answer": "string",
      "status": "pending_review",
      "frequency": 5
    }
  ],
  "total": 150,
  "top_topics": [...]
}

# GET /api/v1/analytics/stats
# Общая статистика использования
Response:
{
  "total_documents": 652,
  "total_queries_today": 245,
  "total_queries_month": 7500,
  "avg_response_time_ms": 850,
  "answer_rate": 0.87,
  "top_categories": [
    {"category": "printers", "count": 120},
    {"category": "network", "count": 95}
  ],
  "quality_metrics": {
    "avg_chunk_length": 803,
    "with_keywords_pct": 91,
    "with_category_pct": 25
  }
}

# GET /api/v1/analytics/quality-report
# Отчет о качестве базы знаний
Response:
{
  "duplicates_count": 0,
  "short_chunks": 15,
  "long_chunks": 42,
  "missing_keywords": 58,
  "recommendations": [...]
}

# POST /api/v1/analytics/export
# Экспорт данных (CSV, JSON)
Body:
{
  "type": "unanswered_questions",
  "format": "csv",
  "filters": {...}
}
```

#### 3. **Configuration API** (`/api/v1/config`)

```python
# GET /api/v1/config/search
# Получить настройки поиска
Response:
{
  "min_similarity": 0.5,
  "top_k": 3,
  "use_hybrid_search": true,
  "enable_reranking": false
}

# PUT /api/v1/config/search
# Обновить настройки поиска
Body:
{
  "min_similarity": 0.6,
  "top_k": 5
}

# GET /api/v1/config/llm
# Получить настройки LLM
Response:
{
  "model": "gigachat",
  "temperature": 0.7,
  "max_tokens": 500,
  "system_prompt": "..."
}

# PUT /api/v1/config/llm
# Обновить настройки LLM
```

---

## 🔐 Безопасность и аутентификация

### Вариант 1: Basic Auth (Простой)

```python
# admin_panel/utils/auth_manager.py
import streamlit as st
from functools import wraps

def check_auth():
    """Проверка аутентификации"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_form()
        st.stop()

def show_login_form():
    """Форма входа"""
    st.title("🔐 Вход в админ-панель")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Войти"):
        # Проверка credentials из .env
        if (username == os.getenv('ADMIN_USERNAME') and 
            password == os.getenv('ADMIN_PASSWORD')):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Неверный username или password")
```

### Вариант 2: JWT Tokens (Продвинутый)

```python
# Для production推荐使用 JWT
import jwt
from datetime import datetime, timedelta

def create_token(username: str) -> str:
    """Создать JWT token"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'role': 'admin'
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')

def verify_token(token: str) -> dict:
    """Проверить JWT token"""
    try:
        return jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### Вариант 3: OAuth2 / Keycloak (Enterprise)

Интеграция с корпоративным SSO если требуется.

---

## 📄 Реализация страниц

### Страница 1: Управление базой знаний (`pages/1_📚_База_знаний.py`)

```python
import streamlit as st
from admin_panel.components.document_editor import DocumentEditor
from admin_panel.components.quality_validator import QualityValidator
from admin_panel.api.rag_api import RAGApi

st.set_page_config(page_title="База знаний", layout="wide")

# Sidebar filters
st.sidebar.header("Фильтры")
category = st.sidebar.selectbox("Категория", ["Все", "printers", "network", ...])
search_query = st.sidebar.text_input("Поиск")

# Main content
st.title("📚 Управление базой знаний RAG")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Список", "➕ Добавить", "✏️ Редактор", "🔍 Анализ"])

with tab1:
    # Таблица документов с пагинацией
    api = RAGApi()
    docs = api.get_documents(category=category, search=search_query)
    
    for doc in docs:
        with st.expander(f"Doc ID: {doc['id'][:8]}... | {doc['metadata'].get('category', 'N/A')}"):
            st.text(doc['content'][:300] + "...")
            st.json(doc['metadata'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️ Редактировать", key=f"edit_{doc['id']}"):
                    st.session_state.edit_doc_id = doc['id']
            with col2:
                if st.button("🗑️ Удалить", key=f"delete_{doc['id']}"):
                    api.delete_document(doc['id'])
                    st.success("Удалено")
            with col3:
                st.write(f"Created: {doc['created_at']}")

with tab2:
    # Форма добавления нового документа
    editor = DocumentEditor()
    editor.show_add_form()

with tab3:
    # Редактор существующего документа
    if 'edit_doc_id' in st.session_state:
        editor = DocumentEditor()
        editor.show_edit_form(st.session_state.edit_doc_id)

with tab4:
    # Анализ качества
    validator = QualityValidator()
    validator.show_quality_report()
```

### Страница 2: Аналитика (`pages/2_📊_Аналитика.py`)

```python
import streamlit as st
import plotly.express as px
from admin_panel.api.analytics_api import AnalyticsApi

st.set_page_config(page_title="Аналитика", layout="wide")

st.title("📊 Мониторинг и аналитика")

# KPI Cards
api = AnalyticsApi()
stats = api.get_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего документов", stats['total_documents'])
col2.metric("Запросов сегодня", stats['total_queries_today'])
col3.metric("Ответов rate", f"{stats['answer_rate']*100:.1f}%")
col4.metric("Avg response", f"{stats['avg_response_time_ms']}ms")

# Charts
tab1, tab2, tab3 = st.tabs(["📈 Использование", "❓ Unanswered", "✅ Качество"])

with tab1:
    # График запросов по времени
    fig = px.line(data_frame=api.get_queries_timeline(), 
                  x='date', y='count',
                  title="Запросы по дням")
    st.plotly_chart(fig, use_container_width=True)
    
    # Top категории
    fig = px.bar(data_frame=stats['top_categories'],
                 x='category', y='count',
                 title="Топ категорий")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Unanswered questions таблица
    unanswered = api.get_unanswered_questions(limit=50)
    st.dataframe(unanswered, use_container_width=True)
    
    # Top topics
    st.subheader("Топ тем unanswered вопросов")
    for topic in unanswered['top_topics'][:10]:
        st.write(f"- {topic['topic']}: {topic['count']} раз")

with tab3:
    # Quality metrics
    quality = api.get_quality_report()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("С keywords", f"{quality['with_keywords_pct']}%")
    col2.metric("С категорией", f"{quality['with_category_pct']}%")
    col3.metric("Дубликатов", quality['duplicates_count'])
    
    # Recommendations
    st.subheader("Рекомендации")
    for rec in quality['recommendations']:
        st.warning(rec)
```

### Страница 3: Настройки (`pages/3_⚙️_Настройки.py`)

```python
import streamlit as st
from admin_panel.api.config_api import ConfigApi

st.set_page_config(page_title="Настройки")

st.title("⚙️ Настройки системы")

tab1, tab2 = st.tabs(["🔍 Поиск", "🤖 LLM"])

with tab1:
    api = ConfigApi()
    config = api.get_search_config()
    
    st.subheader("Параметры поиска")
    
    min_similarity = st.slider(
        "Min Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=config['min_similarity'],
        step=0.05,
        help="Минимальный порог схожести для результатов поиска"
    )
    
    top_k = st.number_input(
        "Top K Results",
        min_value=1,
        max_value=20,
        value=config['top_k'],
        help="Количество возвращаемых результатов"
    )
    
    use_hybrid = st.checkbox(
        "Use Hybrid Search",
        value=config['use_hybrid_search'],
        help="Использовать гибридный поиск (semantic + keyword)"
    )
    
    if st.button("💾 Сохранить настройки поиска"):
        api.update_search_config(
            min_similarity=min_similarity,
            top_k=top_k,
            use_hybrid_search=use_hybrid
        )
        st.success("Настройки сохранены!")

with tab2:
    st.subheader("Параметры LLM")
    # Аналогично для LLM настроек
```

---

## 🐳 Docker конфигурация

### `docker-compose.yml` (добавить сервис)

```yaml
services:
  # Существующие сервисы...
  
  # Новый сервис: Admin Panel
  admin-panel:
    build:
      context: .
      dockerfile: admin_panel/Dockerfile
    ports:
      - "8501:8501"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - JWT_SECRET=${JWT_SECRET:-change_me_in_production}
    volumes:
      - ./data:/app/data
      - ./utils:/app/utils:ro
      - ./rag:/app/rag:ro
    depends_on:
      - max-bot-webhook
    networks:
      - service-desk-network
    restart: unless-stopped
```

### `admin_panel/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY admin_panel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY admin_panel/ ./admin_panel/
COPY utils/ ./utils/
COPY rag/ ./rag/

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "admin_panel/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### `admin_panel/requirements.txt`

```txt
streamlit==1.32.0
streamlit-authenticator==0.3.2
plotly==5.18.0
pandas==2.1.4
supabase==2.3.4
python-dotenv==1.0.0
pyjwt==2.8.0
requests==2.31.0
```

---

## 🚀 План реализации

### Phase 1: MVP (3-5 дней)

**День 1-2: Базовая структура**
- [ ] Создать структуру директорий `admin_panel/`
- [ ] Настроить Docker для admin panel
- [ ] Реализовать базовую аутентификацию (Basic Auth)
- [ ] Создать главную страницу `app.py`

**День 3-4: Управление документами**
- [ ] Реализовать API endpoints для CRUD операций
- [ ] Создать компонент просмотра списка документов
- [ ] Реализовать форму добавления документа с валидацией
- [ ] Интегрировать `DocumentQualityValidator`

**День 5: Деплой и тестирование**
- [ ] Протестировать локально
- [ ] Задеплоить через Docker Compose
- [ ] Documentation

### Phase 2: Аналитика (2-3 дня)

**День 6-7:**
- [ ] Реализовать Analytics API
- [ ] Создать дашборд с графиками (Plotly)
- [ ] Интеграция с `unanswered_questions.json`
- [ ] Экспорт данных (CSV/JSON)

### Phase 3: Продвинутые функции (3-4 дня)

**День 8-10:**
- [ ] Настройки системы (поиск, LLM)
- [ ] Batch operations (импорт/экспорт)
- [ ] Advanced filtering и search
- [ ] Quality analysis tools

### Phase 4: Production readiness (2-3 дня)

**День 11-13:**
- [ ] JWT authentication
- [ ] Rate limiting
- [ ] Logging и monitoring
- [ ] Unit tests
- [ ] Documentation

---

## 📊 Оценка ресурсов

| Этап | Время | Сложность | Приоритет |
|------|-------|-----------|-----------|
| Phase 1 (MVP) | 3-5 дней | Средняя | 🔴 HIGH |
| Phase 2 (Analytics) | 2-3 дня | Средняя | 🟡 MEDIUM |
| Phase 3 (Advanced) | 3-4 дня | Высокая | 🟢 LOW |
| Phase 4 (Production) | 2-3 дня | Средняя | 🟡 MEDIUM |

**Итого:** 10-15 дней для full-featured admin panel

---

## 💡 Рекомендации

### 1. Начните с MVP
- Реализуйте только управление документами
- Добавьте аналитику позже
- Не перегружайте первой версией

### 2. Переиспользуйте существующий код
- `utils/document_validator.py` - готов к использованию
- `utils/safe_document_manager.py` - готов к использованию
- `rag/supabase_manager.py` - готов к использованию

### 3. Безопасность
- Используйте环境变量 для credentials
- Включите HTTPS в production
- Регулярно меняйте пароли

### 4. Масштабируемость
- Streamlit легко мигрировать на React если нужно
- API layer позволяет заменить frontend без изменения backend
- Docker обеспечивает portability

### 5. Monitoring
- Добавьте logging всех действий админа
- Track changes to documents
- Monitor performance metrics

---

## 🎯 Success Criteria

Admin panel считается успешной если:

- ✅ Админ может добавить документ за <2 минут
- ✅ Валидация предотвращает 90%+ проблем качества
- ✅ Unanswered questions просматриваются в реальном времени
- ✅ Настройки поиска изменяются без перезапуска бота
- ✅ Система работает стабильно 24/7

---

## 📞 Next Steps

1. **Утвердить архитектуру** - обсудить с командой
2. **Начать Phase 1** - создать базовую структуру
3. **Weekly reviews** - проверять прогресс
4. **User testing** - получить feedback от admins
5. **Iterate** - улучшать на основе feedback

---

**Готов приступить к реализации? Начнем с Phase 1?** 🚀
