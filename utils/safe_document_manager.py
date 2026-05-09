#!/usr/bin/env python3
"""
Безопасный менеджер для добавления документов в RAG с автоматической валидацией и улучшением качества

Предотвращает появление проблем:
1. Отсутствующие keywords
2. Слишком длинные чанки
3. Отсутствие синонимов
4. Отсутствие категорий
"""

from supabase import create_client
import os
from dotenv import load_dotenv
from utils.document_validator import DocumentQualityValidator
import logging

logger = logging.getLogger(__name__)

# Try to import YandexEmbeddings, fallback to None if not available
try:
    from rag.yandex_embeddings import YandexEmbeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    YandexEmbeddings = None
    EMBEDDINGS_AVAILABLE = False
    logger.warning("YandexEmbeddings not available - embedding generation will be skipped")

load_dotenv()


class SafeDocumentManager:
    """Менеджер для безопасного добавления документов с гарантией качества"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.validator = DocumentQualityValidator()
        
        # Initialize embeddings only if available
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings = YandexEmbeddings()
            except Exception as e:
                logger.warning(f"Failed to initialize YandexEmbeddings: {e}")
                self.embeddings = None
        else:
            self.embeddings = None
        
        self.table_name = 'documents'
    
    def add_document_safe(
        self, 
        content: str, 
        metadata: dict = None,
        auto_fix: bool = True,
        validate_only: bool = False
    ) -> dict:
        """
        Безопасное добавление документа с валидацией и автоисправлениями
        
        Args:
            content: Текст документа
            metadata: Метаданные (опционально)
            auto_fix: Автоматически исправлять проблемы
            validate_only: Только валидация без сохранения
            
        Returns:
            Dict с результатом операции
        """
        metadata = metadata or {}
        
        # Шаг 1: Валидация
        logger.info("Валидация документа...")
        validation_result = self.validator.validate_document(content, metadata)
        
        if not validation_result.is_valid and not auto_fix:
            return {
                'success': False,
                'error': 'Документ не прошел валидацию',
                'validation_report': self.validator.generate_validation_report(content, metadata),
                'score': validation_result.score
            }
        
        # Шаг 2: Применение автоматических исправлений
        if auto_fix:
            logger.info("Применение автоматических исправлений...")
            
            # Добавляем keywords если отсутствуют
            if 'keywords' in validation_result.auto_fixes:
                metadata = self.validator.add_suggested_keywords(metadata, content)
                logger.info(f"✅ Добавлены keywords: {metadata['keywords'][:5]}")
            
            # Добавляем категорию если отсутствует
            if 'category' in validation_result.auto_fixes:
                metadata = self.validator.add_suggested_category(metadata, content)
                logger.info(f"✅ Добавлена категория: {metadata.get('category')}")
            
            # Добавляем синонимы
            improved_content = self.validator.suggest_synonyms_addition(content)
            if improved_content != content:
                content = improved_content
                logger.info("✅ Добавлены синонимы")
            
            # Разбиваем длинные чанки
            if len(content) > self.validator.max_chunk_length:
                chunks = self.validator.split_long_chunk(content)
                logger.info(f"⚠️  Чанк разбит на {len(chunks)} частей")
                
                # Рекурсивно добавляем каждый чанк
                results = []
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['total_chunks'] = len(chunks)
                    
                    result = self._save_single_document(chunk, chunk_metadata)
                    results.append(result)
                
                return {
                    'success': all(r['success'] for r in results),
                    'chunks_added': len(results),
                    'results': results,
                    'validation_score': validation_result.score
                }
        
        # Шаг 3: Сохранение одиночного документа
        if validate_only:
            return {
                'success': True,
                'validate_only': True,
                'validation_report': self.validator.generate_validation_report(content, metadata),
                'score': validation_result.score,
                'metadata': metadata
            }
        
        return self._save_single_document(content, metadata)
    
    def _save_single_document(self, content: str, metadata: dict) -> dict:
        """Сохраняет одиночный документ в базу"""
        try:
            # Генерируем embeddings если доступно
            embedding = None
            if self.embeddings:
                try:
                    embedding = self.embeddings.get_embeddings(content)
                except Exception as e:
                    logger.warning(f"Failed to generate embeddings: {e}")
            
            # Подготавливаем данные
            doc_data = {
                'content': content,
                'metadata': metadata
            }
            
            # Добавляем embedding только если он есть
            if embedding:
                doc_data['embedding'] = embedding
            
            # Сохраняем в Supabase
            result = self.supabase.table(self.table_name).insert(doc_data).execute()
            
            if result.data:
                doc_id = result.data[0]['id']
                logger.info(f"✅ Документ сохранен: {doc_id}")
                
                return {
                    'success': True,
                    'document_id': doc_id,
                    'metadata': metadata
                }
            else:
                return {
                    'success': False,
                    'error': 'Не удалось сохранить документ'
                }
        
        except Exception as e:
            logger.error(f"Ошибка сохранения документа: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_qa_pair_safe(
        self,
        question: str,
        answer: str,
        category: str = None,
        auto_fix: bool = True
    ) -> dict:
        """
        Безопасное добавление пары вопрос-ответ
        
        Args:
            question: Вопрос пользователя
            answer: Ответ с решением
            category: Категория (опционально, определится автоматически)
            auto_fix: Автоматические исправления
            
        Returns:
            Результат операции
        """
        # Формируем контент в формате Q&A
        content = f"В: {question}\nО: {answer}"
        
        # Формируем базовые метаданные
        metadata = {
            'type': 'faq',
            'format': 'qa'
        }
        
        if category:
            metadata['category'] = category
        
        # Добавляем с валидацией
        return self.add_document_safe(content, metadata, auto_fix=auto_fix)
    
    def batch_add_documents_safe(
        self,
        documents: list,
        auto_fix: bool = True
    ) -> dict:
        """
        Пакетное добавление документов с валидацией
        
        Args:
            documents: Список dicts с ключами 'content' и 'metadata'
            auto_fix: Автоматические исправления
            
        Returns:
            Статистика операции
        """
        total = len(documents)
        success_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        
        logger.info(f"Начало пакетной загрузки {total} документов...")
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"Обработка {i}/{total}...")
            
            result = self.add_document_safe(
                content=doc['content'],
                metadata=doc.get('metadata', {}),
                auto_fix=auto_fix
            )
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
            
            results.append(result)
        
        summary = {
            'total': total,
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'success_rate': (success_count / total * 100) if total > 0 else 0,
            'results': results
        }
        
        logger.info(f"Пакетная загрузка завершена: {success_count}/{total} успешно")
        
        return summary
    
    def validate_before_add(self, content: str, metadata: dict = None) -> dict:
        """
        Предварительная валидация без сохранения
        
        Args:
            content: Текст документа
            metadata: Метаданные
            
        Returns:
            Результат валидации
        """
        return self.add_document_safe(
            content=content,
            metadata=metadata,
            auto_fix=False,
            validate_only=True
        )


def main():
    """Пример использования SafeDocumentManager"""
    
    manager = SafeDocumentManager()
    
    print("=" * 80)
    print("ТЕСТ БЕЗОПАСНОГО ДОБАВЛЕНИЯ ДОКУМЕНТОВ")
    print("=" * 80)
    
    # Тест 1: Проблема без keywords и категории
    print("\n📝 Тест 1: Документ без keywords и категории")
    test_content_1 = """В: Как подключить принтер?
О: Подключите принтер к компьютеру через USB кабель. Установите драйверы с диска."""
    
    result_1 = manager.add_document_safe(
        content=test_content_1,
        metadata={},
        auto_fix=True,
        validate_only=True
    )
    
    print(f"Статус: {'✅' if result_1['success'] else '❌'}")
    print(f"Оценка: {result_1['score']}/100")
    print(f"Metadata после автоисправлений: {result_1.get('metadata', {})}")
    
    # Тест 2: Добавление Q&A пары
    print("\n📝 Тест 2: Добавление Q&A пары")
    result_2 = manager.add_qa_pair_safe(
        question="Как настроить Wi-Fi?",
        answer="Откройте настройки сети. Выберите вашу Wi-Fi сеть. Введите пароль.",
        auto_fix=True
    )
    
    print(f"Результат: {result_2}")
    
    # Тест 3: Предварительная валидация
    print("\n📝 Тест 3: Предварительная валидация problematic документа")
    problematic_content = "Просто какой-то текст без формата Q&A и очень длинный " * 20
    
    validation = manager.validate_before_add(problematic_content)
    print(f"Валидация пройдена: {validation['success']}")
    print(f"Оценка: {validation['score']}/100")
    
    print("\n" + "=" * 80)
    print("Для реального добавления используйте:")
    print("  manager.add_document_safe(content, metadata, auto_fix=True)")
    print("  manager.add_qa_pair_safe(question, answer, auto_fix=True)")
    print("=" * 80)


if __name__ == '__main__':
    main()
