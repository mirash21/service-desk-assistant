"""
Rate Limiter для защиты от спама
"""
import time
from collections import defaultdict
from utils.logger import logger


class RateLimiter:
    """Ограничение частоты запросов от пользователей"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: Максимальное количество запросов
            window_seconds: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(list)
        logger.info(f"RateLimiter инициализирован: {max_requests} запросов за {window_seconds} сек")

    def is_allowed(self, user_id: str) -> bool:
        """
        Проверка, может ли пользователь отправить запрос
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если запрос разрешен, False если превышен лимит
        """
        now = time.time()
        
        # Очищаем старые запросы
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit превышен для пользователя {user_id}")
            return False
        
        # Записываем новый запрос
        self.user_requests[user_id].append(now)
        return True

    def get_remaining_requests(self, user_id: str) -> int:
        """
        Получить количество оставшихся запросов
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество оставшихся запросов
        """
        now = time.time()
        recent_requests = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(recent_requests))
