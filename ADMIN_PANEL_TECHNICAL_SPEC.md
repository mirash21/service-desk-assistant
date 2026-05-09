# Technical Specification: Admin Panel Phase 1 (MVP)

**Version:** 1.0  
**Date:** April 27, 2026  
**Status:** 📋 Ready for Implementation

---

## 🎯 Objective

Create a minimal viable admin panel for managing RAG knowledge base with document CRUD operations and quality validation.

---

## 📋 Requirements

### Functional Requirements

1. **Authentication**
   - Basic username/password login
   - Session management
   - Logout functionality

2. **Document Management**
   - View list of documents with pagination
   - Filter by category
   - Search by content
   - Add new document with validation
   - Edit existing document
   - Delete document
   - View document details

3. **Quality Validation**
   - Real-time validation when adding/editing
   - Show validation score
   - Display warnings and suggestions
   - Auto-fix options (keywords, category)

4. **Basic Analytics**
   - Total documents count
   - Documents by category
   - Quality metrics overview

### Non-Functional Requirements

- Response time < 2 seconds for all operations
- Support up to 1000 documents in database
- Mobile-friendly interface
- Docker deployment ready
- No external dependencies beyond Python ecosystem

---

## 🏗️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────┐
│         Streamlit Application           │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌────────────────┐  │
│  │   Pages      │  │  Components    │  │
│  │              │  │                │  │
│  │ • Login      │  │ • DocEditor    │  │
│  │ • Documents  │  │ • Validator    │  │
│  │ • Analytics  │  │ • AuthForm     │  │
│  └──────┬───────┘  └────────┬───────┘  │
│         │                   │           │
│         └────────┬──────────┘           │
│                  │                      │
│         ┌────────▼────────┐            │
│         │   API Layer     │            │
│         │                 │            │
│         │ • RAGApi        │            │
│         │ • AnalyticsApi  │            │
│         └────────┬────────┘            │
│                  │                      │
└──────────────────┼──────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Supabase Client   │
         │  (existing)        │
         └────────────────────┘
```

---

## 📁 File Structure

```
admin_panel/
├── __init__.py
├── app.py                          # Main entry point
├── requirements.txt                # Dependencies
├── Dockerfile                      # Docker configuration
│
├── pages/
│   ├── 0_🔐_Login.py              # Login page
│   ├── 1_📚_Documents.py          # Document management
│   └── 2_📊_Analytics.py          # Basic analytics
│
├── components/
│   ├── __init__.py
│   ├── auth_form.py               # Login form component
│   ├── document_table.py          # Document list table
│   ├── document_editor.py         # Add/Edit form
│   └── quality_indicator.py       # Validation display
│
├── api/
│   ├── __init__.py
│   ├── rag_api.py                 # Document CRUD operations
│   └── analytics_api.py           # Statistics endpoints
│
└── utils/
    ├── __init__.py
    ├── session_manager.py         # Session state helper
    └── style.py                   # Custom CSS styles
```

---

## 🔧 Implementation Details

### 1. Main Application (`app.py`)

```python
import streamlit as st
from admin_panel.utils.session_manager import initialize_session
from admin_panel.utils.style import load_custom_css

# Page config
st.set_page_config(
    page_title="Service Desk Admin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session()

# Load custom styles
load_custom_css()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("pages/0_🔐_Login.py")
else:
    # Show sidebar navigation
    with st.sidebar:
        st.title("🤖 Admin Panel")
        st.write(f"Welcome, {st.session_state.get('username', 'Admin')}!")
        st.divider()
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
    
    # Main content will be loaded from pages
    st.title("Service Desk Assistant - Admin Panel")
    st.info("Select a page from the sidebar to get started.")
```

### 2. Authentication (`components/auth_form.py`)

```python
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def show_login_form():
    """Display login form"""
    st.title("🔐 Admin Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if validate_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def validate_credentials(username: str, password: str) -> bool:
    """Validate credentials against environment variables"""
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    return username == admin_user and password == admin_pass
```

### 3. RAG API (`api/rag_api.py`)

```python
from supabase import create_client
import os
from dotenv import load_dotenv
from utils.safe_document_manager import SafeDocumentManager
from utils.document_validator import DocumentQualityValidator
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class RAGApi:
    """API for RAG document operations"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.manager = SafeDocumentManager()
        self.validator = DocumentQualityValidator()
        self.table_name = 'documents'
    
    def get_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict:
        """Get paginated list of documents"""
        
        # Build query
        query = self.supabase.table(self.table_name).select(
            'id', 'content', 'metadata', 'created_at'
        )
        
        # Apply filters
        if category and category != 'Все':
            query = query.eq('metadata->>category', category)
        
        # Execute query with pagination
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        result = query.range(start, end).execute()
        
        # Get total count
        count_result = self.supabase.table(self.table_name).select(
            'id', count='exact'
        )
        if category and category != 'Все':
            count_result = count_result.eq('metadata->>category', category)
        count_result = count_result.execute()
        
        total = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return {
            'documents': result.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def add_document(
        self,
        content: str,
        metadata: Dict = None,
        auto_fix: bool = True
    ) -> Dict:
        """Add new document with validation"""
        
        # Validate first
        validation = self.validator.validate_document(content, metadata or {})
        
        if not validation.is_valid and not auto_fix:
            return {
                'success': False,
                'error': 'Validation failed',
                'validation_report': validation
            }
        
        # Add with safe manager
        result = self.manager.add_document_safe(
            content=content,
            metadata=metadata,
            auto_fix=auto_fix
        )
        
        return result
    
    def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict = None
    ) -> Dict:
        """Update existing document"""
        try:
            # First delete old embedding
            self.supabase.table(self.table_name).delete().eq('id', doc_id).execute()
            
            # Generate new embedding
            from rag.yandex_embeddings import YandexEmbeddings
            embeddings = YandexEmbeddings()
            embedding = embeddings.get_embeddings(content)
            
            # Insert updated document
            doc_data = {
                'id': doc_id,
                'content': content,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            result = self.supabase.table(self.table_name).insert(doc_data).execute()
            
            return {
                'success': True,
                'document_id': doc_id
            }
        
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_document(self, doc_id: str) -> Dict:
        """Delete document"""
        try:
            result = self.supabase.table(self.table_name).delete().eq('id', doc_id).execute()
            
            return {
                'success': True,
                'document_id': doc_id
            }
        
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_document(
        self,
        content: str,
        metadata: Dict = None
    ) -> Dict:
        """Validate document without saving"""
        
        validation = self.validator.validate_document(content, metadata or {})
        
        return {
            'is_valid': validation.is_valid,
            'score': validation.score,
            'issues': validation.issues,
            'warnings': validation.warnings,
            'suggestions': validation.suggestions,
            'auto_fixes': validation.auto_fixes
        }
```

### 4. Document Management Page (`pages/1_📚_Documents.py`)

```python
import streamlit as st
from admin_panel.api.rag_api import RAGApi
from admin_panel.components.document_table import show_document_table
from admin_panel.components.document_editor import show_add_document_form

st.set_page_config(page_title="Documents", layout="wide")

st.title("📚 Knowledge Base Management")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    
    category = st.selectbox(
        "Category",
        ["Все", "printers", "network", "email", "password", 
         "software", "hardware", "security", "windows", "office"]
    )
    
    search_query = st.text_input("Search in content")
    
    if st.button("Apply Filters"):
        st.session_state.filter_category = category
        st.session_state.filter_search = search_query

# Tabs
tab1, tab2 = st.tabs(["📋 Browse Documents", "➕ Add New"])

with tab1:
    # Get filter values
    category = st.session_state.get('filter_category', 'Все')
    search = st.session_state.get('filter_search', '')
    
    # Show document table
    api = RAGApi()
    show_document_table(api, category=category, search=search)

with tab2:
    # Show add form
    show_add_document_form()
```

### 5. Document Table Component (`components/document_table.py`)

```python
import streamlit as st
from admin_panel.api.rag_api import RAGApi

def show_document_table(api: RAGApi, category: str = 'Все', search: str = ''):
    """Display documents in a table with actions"""
    
    # Pagination
    if 'page' not in st.session_state:
        st.session_state.page = 1
    
    page_size = 20
    
    # Fetch documents
    result = api.get_documents(
        page=st.session_state.page,
        page_size=page_size,
        category=category,
        search=search
    )
    
    docs = result['documents']
    total = result['total']
    total_pages = result['total_pages']
    
    # Display info
    st.write(f"Showing {len(docs)} of {total} documents")
    
    # Display documents
    for doc in docs:
        with st.expander(
            f"📄 {doc['id'][:8]}... | Category: {doc['metadata'].get('category', 'N/A')}"
        ):
            # Content preview
            st.text_area(
                "Content",
                value=doc['content'],
                height=150,
                disabled=True,
                key=f"content_{doc['id']}"
            )
            
            # Metadata
            st.json(doc['metadata'])
            
            # Actions
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✏️ Edit", key=f"edit_{doc['id']}"):
                    st.session_state.edit_doc_id = doc['id']
                    st.session_state.edit_doc_content = doc['content']
                    st.session_state.edit_doc_metadata = doc['metadata']
                    st.switch_page("pages/1_📚_Documents.py")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{doc['id']}"):
                    if confirm_delete(doc['id']):
                        result = api.delete_document(doc['id'])
                        if result['success']:
                            st.success("Document deleted")
                            st.rerun()
                        else:
                            st.error(f"Error: {result['error']}")
            
            with col3:
                st.caption(f"Created: {doc['created_at']}")
    
    # Pagination controls
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.page > 1:
                if st.button("← Previous"):
                    st.session_state.page -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Page {st.session_state.page} of {total_pages}")
        
        with col3:
            if st.session_state.page < total_pages:
                if st.button("Next →"):
                    st.session_state.page += 1
                    st.rerun()

def confirm_delete(doc_id: str) -> bool:
    """Show confirmation dialog"""
    return st.checkbox(f"Confirm delete {doc_id[:8]}...", key=f"confirm_{doc_id}")
```

### 6. Document Editor Component (`components/document_editor.py`)

```python
import streamlit as st
from admin_panel.api.rag_api import RAGApi
from admin_panel.components.quality_indicator import show_validation_result

def show_add_document_form():
    """Form for adding new document"""
    
    st.header("Add New Document")
    
    with st.form("add_document_form"):
        # Category selection
        category = st.selectbox(
            "Category",
            ["printers", "network", "email", "password", 
             "software", "hardware", "security", "windows", "office", "general"]
        )
        
        # Question
        question = st.text_area(
            "Question (В: ...)",
            placeholder="В: How to connect printer?",
            height=100
        )
        
        # Answer
        answer = st.text_area(
            "Answer (О: ...)",
            placeholder="О: Connect via USB cable...",
            height=200
        )
        
        # Auto-fix option
        auto_fix = st.checkbox("Enable auto-fix (recommended)", value=True)
        
        # Preview validation
        if st.form_submit_button("Preview Validation"):
            if question and answer:
                content = f"В: {question}\nО: {answer}"
                metadata = {'category': category, 'type': 'faq'}
                
                api = RAGApi()
                validation = api.validate_document(content, metadata)
                
                show_validation_result(validation)
        
        # Submit
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Document", type="primary"):
                if not question or not answer:
                    st.error("Please fill in both question and answer")
                else:
                    content = f"В: {question}\nО: {answer}"
                    metadata = {'category': category, 'type': 'faq', 'format': 'qa'}
                    
                    api = RAGApi()
                    result = api.add_document(
                        content=content,
                        metadata=metadata,
                        auto_fix=auto_fix
                    )
                    
                    if result['success']:
                        st.success(f"✅ Document added! ID: {result.get('document_id', 'N/A')}")
                        st.balloons()
                        
                        # Clear form
                        st.session_state.question = ""
                        st.session_state.answer = ""
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        with col2:
            if st.form_submit_button("🔄 Clear Form"):
                st.rerun()

def show_edit_document_form(doc_id: str, content: str, metadata: dict):
    """Form for editing existing document"""
    
    st.header(f"Edit Document {doc_id[:8]}")
    
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
        category = st.selectbox(
            "Category",
            ["printers", "network", "email", "password", 
             "software", "hardware", "security", "windows", "office", "general"],
            index=["printers", "network", "email", "password", 
                   "software", "hardware", "security", "windows", "office", "general"].index(
                       metadata.get('category', 'general')
                   ) if metadata.get('category') in ["printers", "network", "email", "password", 
                   "software", "hardware", "security", "windows", "office", "general"] else 9
        )
        
        question = st.text_area("Question", value=question, height=100)
        answer = st.text_area("Answer", value=answer, height=200)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Update", type="primary"):
                content = f"В: {question}\nО: {answer}"
                metadata['category'] = category
                
                api = RAGApi()
                result = api.update_document(doc_id, content, metadata)
                
                if result['success']:
                    st.success("Document updated!")
                    del st.session_state.edit_doc_id
                    st.rerun()
                else:
                    st.error(f"Error: {result['error']}")
        
        with col2:
            if st.form_submit_button("Cancel"):
                del st.session_state.edit_doc_id
                st.rerun()
```

### 7. Quality Indicator (`components/quality_indicator.py`)

```python
import streamlit as st

def show_validation_result(validation: dict):
    """Display validation results"""
    
    st.subheader("Validation Results")
    
    # Score indicator
    score = validation['score']
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if score >= 80:
            st.metric("Quality Score", f"{score}/100", delta="Good")
        elif score >= 60:
            st.metric("Quality Score", f"{score}/100", delta="Fair")
        else:
            st.metric("Quality Score", f"{score}/100", delta="Poor", delta_color="inverse")
    
    with col2:
        if validation['is_valid']:
            st.success("✅ Document is valid")
        else:
            st.error("❌ Document needs improvements")
    
    # Issues
    if validation['issues']:
        st.warning("Issues:")
        for issue in validation['issues']:
            st.write(f"- {issue}")
    
    # Warnings
    if validation['warnings']:
        st.info("Warnings:")
        for warning in validation['warnings']:
            st.write(f"- {warning}")
    
    # Suggestions
    if validation['suggestions']:
        st.info("Suggestions:")
        for suggestion in validation['suggestions']:
            st.write(f"- {suggestion}")
    
    # Auto-fixes
    if validation['auto_fixes']:
        st.success("Auto-fixes available:")
        for fix_type, fix_value in validation['auto_fixes'].items():
            st.write(f"- **{fix_type}:** {fix_value}")
```

---

## 🧪 Testing Plan

### Unit Tests

```python
# tests/test_rag_api.py
import pytest
from admin_panel.api.rag_api import RAGApi

def test_get_documents():
    api = RAGApi()
    result = api.get_documents(page=1, page_size=10)
    
    assert 'documents' in result
    assert 'total' in result
    assert len(result['documents']) <= 10

def test_validate_document():
    api = RAGApi()
    
    content = "В: Test question?\nО: Test answer."
    metadata = {'category': 'test'}
    
    result = api.validate_document(content, metadata)
    
    assert 'is_valid' in result
    assert 'score' in result
```

### Manual Testing Checklist

- [ ] Login with correct credentials
- [ ] Login with incorrect credentials (should fail)
- [ ] View document list
- [ ] Filter by category
- [ ] Search documents
- [ ] Add new document
- [ ] Validate document before saving
- [ ] Edit existing document
- [ ] Delete document with confirmation
- [ ] Pagination works correctly
- [ ] Logout functionality

---

## 📦 Dependencies

### `admin_panel/requirements.txt`

```txt
streamlit==1.32.0
supabase==2.3.4
python-dotenv==1.0.0
plotly==5.18.0
pandas==2.1.4
```

---

## 🚀 Deployment

### Local Development

```bash
# Navigate to project root
cd /home/mirash/service-desk-assistant

# Run admin panel
streamlit run admin_panel/app.py --server.port=8501
```

### Docker Deployment

```bash
# Build and run with docker-compose
docker compose up -d admin-panel

# Access at http://localhost:8501
```

---

## 📊 Success Metrics

- ✅ Admin can view all documents in <2 seconds
- ✅ Adding a document takes <1 minute
- ✅ Validation catches 90%+ of quality issues
- ✅ Zero data loss during CRUD operations
- ✅ UI is intuitive (no training required)

---

## 🎯 Next Steps After MVP

1. Add advanced filtering (date range, quality score)
2. Implement batch operations (import/export)
3. Add real-time analytics dashboard
4. Implement user activity logging
5. Add backup/restore functionality

---

**Ready to implement? Start with `app.py` and work through each component!** 🚀
