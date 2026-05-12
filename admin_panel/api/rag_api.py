"""
RAG API - CRUD operations for documents
"""

from supabase import create_client
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging
import sys

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, '/app')

from utils.safe_document_manager import SafeDocumentManager
from utils.document_validator import DocumentQualityValidator

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
        ).order('created_at', desc=True)
        
        # Apply category filter
        if category and category != 'Все':
            # Filter by metadata->>category
            result = query.execute()
            docs = [
                doc for doc in result.data 
                if doc.get('metadata', {}).get('category') == category
            ]
        else:
            result = query.execute()
            docs = result.data
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            docs = [
                doc for doc in docs
                if search_lower in doc.get('content', '').lower()
            ]
        
        # Pagination
        total = len(docs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = docs[start:end]
        
        return {
            'documents': paginated_docs,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    def add_document(
        self,
        content: str,
        metadata: Dict = None,
        auto_fix: bool = True
    ) -> Dict:
        """Add new document with validation"""
        
        try:
            # Validate first
            validation = self.validator.validate_document(content, metadata or {})
            
            if not validation.is_valid and not auto_fix:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_score': validation.score,
                    'issues': validation.issues
                }
            
            # Add with safe manager
            result = self.manager.add_document_safe(
                content=content,
                metadata=metadata,
                auto_fix=auto_fix
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict = None
    ) -> Dict:
        """Update existing document"""
        try:
            from rag.yandex_embeddings import YandexEmbeddings
            
            # Generate new embedding
            embeddings = YandexEmbeddings()
            embedding = embeddings.get_embeddings(content)
            
            # Update document
            doc_data = {
                'content': content,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            result = self.supabase.table(self.table_name).update(doc_data).eq('id', doc_id).execute()
            
            if result.data:
                return {
                    'success': True,
                    'document_id': doc_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Document not found'
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
        
        try:
            validation = self.validator.validate_document(content, metadata or {})
            
            return {
                'is_valid': validation.is_valid,
                'score': validation.score,
                'issues': validation.issues,
                'warnings': validation.warnings,
                'suggestions': validation.suggestions,
                'auto_fixes': validation.auto_fixes
            }
        
        except Exception as e:
            logger.error(f"Error validating document: {e}")
            return {
                'is_valid': False,
                'score': 0,
                'issues': [f"Validation error: {str(e)}"],
                'warnings': [],
                'suggestions': [],
                'auto_fixes': {}
            }
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get single document by ID"""
        try:
            result = self.supabase.table(self.table_name).select(
                'id', 'content', 'metadata', 'created_at'
            ).eq('id', doc_id).execute()
            
            if result.data:
                return result.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching document: {e}")
            return None
    
    def get_categories(self) -> List[str]:
        """Get list of unique categories"""
        try:
            result = self.supabase.table(self.table_name).select('metadata').execute()
            
            categories = set()
            for doc in result.data:
                category = doc.get('metadata', {}).get('category')
                if category:
                    categories.add(category)
            
            return sorted(list(categories))
        
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []
    
    def get_chat_history(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Get chat history with server-side pagination"""
        try:
            # Сначала получаем общее количество записей
            count_query = self.supabase.table('chat_history').select('id', count='exact')
            
            if user_id:
                count_query = count_query.eq('user_id', user_id)
            
            count_result = count_query.execute()
            total = count_result.count if hasattr(count_result, 'count') else 0
            
            # Затем получаем только нужную страницу
            query = self.supabase.table('chat_history').select(
                'id', 'user_id', 'message_type', 'content', 'metadata', 'created_at'
            ).order('created_at', desc=True)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            # Server-side pagination
            start = (page - 1) * page_size
            end = start + page_size - 1
            query = query.range(start, end)
            
            result = query.execute()
            messages = result.data if result.data else []
            
            return {
                'messages': messages,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            return {
                'messages': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
    
    def get_unique_users(self) -> List[str]:
        """Get list of unique user IDs using DISTINCT query"""
        try:
            # Используем DISTINCT для получения уникальных значений
            result = self.supabase.table('chat_history').select('user_id').execute()
            
            if not result.data:
                return []
            
            # Извлекаем уникальные user_id
            user_ids = set(record.get('user_id') for record in result.data if record.get('user_id'))
            
            return sorted(list(user_ids))
        
        except Exception as e:
            logger.error(f"Error fetching unique users: {e}")
            return []
    
    def get_user_stats(self) -> Dict:
        """Get statistics about users using aggregated query"""
        try:
            # Загружаем только необходимые поля
            result = self.supabase.table('chat_history').select('user_id', 'message_type').execute()
            
            if not result.data:
                return {}
            
            # Агрегируем данные в памяти
            user_stats = {}
            for record in result.data:
                user_id = record.get('user_id')
                message_type = record.get('message_type')
                
                if not user_id:
                    continue
                
                if user_id not in user_stats:
                    user_stats[user_id] = {'user_messages': 0, 'bot_messages': 0, 'total': 0}
                
                if message_type == 'user':
                    user_stats[user_id]['user_messages'] += 1
                elif message_type == 'bot':
                    user_stats[user_id]['bot_messages'] += 1
                
                user_stats[user_id]['total'] += 1
            
            return user_stats
        
        except Exception as e:
            logger.error(f"Error fetching user stats: {e}")
            return {}
