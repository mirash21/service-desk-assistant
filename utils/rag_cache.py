"""
Менеджер кэширования RAG ответов

Кэширует ответы на основе хэша вопроса для ускорения обработки повторяющихся запросов.
Использует JSON файл для хранения кэша с TTL (временем жизни).
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import logger


class RAGCacheManager:
    """Менеджер кэширования RAG ответов"""
    
    def __init__(self, cache_file: str = "data/rag_cache.json", ttl_hours: int = 24):
        """
        Инициализация менеджера кэша
        
        Args:
            cache_file: Путь к файлу кэша
            ttl_hours: Время жизни кэша в часах (по умолчанию 24)
        """
        self.cache_file = Path(cache_file)
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir = self.cache_file.parent
        
        # Создаем директорию если не существует
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем кэш из файла
        self.cache = self._load_cache()
        
        logger.info(f"RAGCacheManager инициализирован: {cache_file}, TTL={ttl_hours}ч")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Загружает кэш из файла"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    logger.info(f"Кэш загружен: {len(cache_data)} записей")
                    return cache_data
            except Exception as e:
                logger.error(f"Ошибка загрузки кэша: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Сохраняет кэш в файл"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Кэш сохранен: {len(self.cache)} записей")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")
    
    def _generate_key(self, question: str, top_k: int = 3) -> str:
        """
        Генерирует ключ кэша на основе вопроса и top_k
        
        Args:
            question: Текст вопроса
            top_k: Количество контекстов
            
        Returns:
            Хэш ключ для кэша
        """
        # Нормализуем вопрос (нижний регистр, убираем лишние пробелы)
        normalized = ' '.join(question.lower().split())
        
        # Создаем хэш
        key_string = f"{normalized}|top_k={top_k}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, question: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """
        Получает ответ из кэша
        
        Args:
            question: Текст вопроса
            top_k: Количество контекстов
            
        Returns:
            Кэшированный ответ или None если не найден/устарел
        """
        key = self._generate_key(question, top_k)
        
        if key not in self.cache:
            logger.debug(f"Кэш промах: {question[:50]}...")
            return None
        
        cached_item = self.cache[key]
        
        # Проверяем время жизни
        cached_time = datetime.fromisoformat(cached_item['timestamp'])
        if datetime.now() - cached_time > self.ttl:
            logger.debug(f"Кэш устарел: {question[:50]}...")
            del self.cache[key]
            self._save_cache()
            return None
        
        logger.debug(f"Кэш попадание: {question[:50]}...")
        return {
            'answer': cached_item['answer'],
            'contexts': cached_item['contexts'],
            'cached_at': cached_item['timestamp']
        }
    
    def set(self, question: str, answer: str, contexts: list, top_k: int = 3):
        """
        Сохраняет ответ в кэш
        
        Args:
            question: Текст вопроса
            answer: Ответ от LLM
            contexts: Список контекстов использованных для ответа
            top_k: Количество контекстов
        """
        key = self._generate_key(question, top_k)
        
        self.cache[key] = {
            'question': question,
            'answer': answer,
            'contexts': contexts,
            'top_k': top_k,
            'timestamp': datetime.now().isoformat()
        }
        
        self._save_cache()
        logger.debug(f"Кэш сохранен: {question[:50]}...")
    
    def clear(self):
        """Очищает весь кэш"""
        self.cache = {}
        self._save_cache()
        logger.info("Кэш очищен")
    
    def cleanup_expired(self):
        """Удаляет устаревшие записи из кэша"""
        now = datetime.now()
        expired_keys = []
        
        for key, item in self.cache.items():
            cached_time = datetime.fromisoformat(item['timestamp'])
            if now - cached_time > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Удалено {len(expired_keys)} устаревших записей из кэша")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику кэша
        
        Returns:
            Словарь со статистикой
        """
        total = len(self.cache)
        
        # Подсчитываем актуальные и устаревшие
        now = datetime.now()
        valid = 0
        expired = 0
        
        for item in self.cache.values():
            cached_time = datetime.fromisoformat(item['timestamp'])
            if now - cached_time <= self.ttl:
                valid += 1
            else:
                expired += 1
        
        # Размер файла
        file_size = self.cache_file.stat().st_size if self.cache_file.exists() else 0
        
        return {
            'total_entries': total,
            'valid_entries': valid,
            'expired_entries': expired,
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'ttl_hours': self.ttl.total_seconds() / 3600
        }
