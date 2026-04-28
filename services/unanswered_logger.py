"""
Сервис для логирования неразрешенных вопросов (Unanswered Questions Log)
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
import logging
import fcntl

logger = logging.getLogger("service_desk")

UNANSWERED_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "unanswered_questions.json")


class UnansweredQuestionsLogger:
    """Сервис для логирования вопросов, на которые бот не смог ответить"""

    def __init__(self, log_path: str = None):
        self.log_path = log_path or UNANSWERED_LOG_PATH
        # Создаём директорию data если её нет
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        # Инициализируем файл если не существует
        if not os.path.exists(self.log_path):
            self._initialize_log_file()
        logger.info(f"UnansweredQuestionsLogger инициализирован: {self.log_path}")

    def _initialize_log_file(self):
        """Инициализирует файл логов пустым массивом"""
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    def _read_log(self) -> list:
        """Читает логи с блокировкой файла для атомарности"""
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Файл логов поврежден или отсутствует, создаю новый")
            self._initialize_log_file()
            return []

    def _write_log(self, data: list):
        """Записывает логи с эксклюзивной блокировкой для атомарности"""
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                try:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
        except Exception as e:
            logger.error(f"Ошибка записи в файл логов: {e}", exc_info=True)
            raise

    def log_unanswered_question(
        self,
        question: str,
        user_id: str,
        suggested_answer: Optional[str] = None,
        context: Optional[str] = None,
        has_image: bool = False,
        mode: str = "rag"
    ) -> dict:
        """
        Логирует вопрос, на который бот не смог ответить
        
        Args:
            question: Текст вопроса пользователя
            user_id: ID пользователя
            suggested_answer: Черновик ответа от LLM (если был сгенерирован)
            context: Контекст обращения (IMAGE_TEXT, VOICE_TEXT и т.д.)
            has_image: Был ли вопрос связан с изображением
            mode: Режим работы бота (rag/text/voice)
            
        Returns:
            Словарь с данными записи
        """
        record = {
            "id": str(uuid.uuid4()),
            "question": question.strip(),
            "user_id": user_id,
            "suggested_answer": suggested_answer.strip() if suggested_answer else None,
            "context": context,
            "has_image": has_image,
            "mode": mode,
            "status": "pending_review",  # pending_review, approved, rejected
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "added_to_rag": False
        }

        # Читаем текущие логи
        logs = self._read_log()
        
        # Добавляем новую запись
        logs.append(record)
        
        # Записываем обратно
        self._write_log(logs)
        
        logger.info(f"Записан неразрешенный вопрос от {user_id}: {question[:50]}...")
        return record

    def get_pending_questions(self, limit: int = 50, offset: int = 0) -> list:
        """
        Получает список вопросов на рассмотрении
        
        Args:
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список записей со статусом pending_review
        """
        logs = self._read_log()
        pending = [log for log in logs if log.get("status") == "pending_review"]
        
        # Сортируем по дате создания (новые первые)
        pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return pending[offset:offset + limit]

    def update_answer(self, record_id: str, answer: str, reviewer: str = "admin") -> bool:
        """
        Обновляет ответ и меняет статус на approved
        
        Args:
            record_id: ID записи
            answer: Подтвержденный ответ
            reviewer: Кто подтвердил
            
        Returns:
            True если обновление успешно
        """
        logs = self._read_log()
        
        for record in logs:
            if record.get("id") == record_id:
                record["suggested_answer"] = answer
                record["status"] = "approved"
                record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                record["reviewed_by"] = reviewer
                break
        else:
            logger.warning(f"Запись с ID {record_id} не найдена")
            return False
        
        self._write_log(logs)
        logger.info(f"Ответ обновлен для записи {record_id}")
        return True

    def reject_question(self, record_id: str, reason: str = "", reviewer: str = "admin") -> bool:
        """
        Отклоняет вопрос (например, если он некорректный или дубликат)
        
        Args:
            record_id: ID записи
            reason: Причина отклонения
            reviewer: Кто отклонил
            
        Returns:
            True если обновление успешно
        """
        logs = self._read_log()
        
        for record in logs:
            if record.get("id") == record_id:
                record["status"] = "rejected"
                record["rejection_reason"] = reason
                record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                record["reviewed_by"] = reviewer
                break
        else:
            logger.warning(f"Запись с ID {record_id} не найдена")
            return False
        
        self._write_log(logs)
        logger.info(f"Запись {record_id} отклонена")
        return True

    def get_statistics(self) -> dict:
        """
        Получает статистику по неразрешенным вопросам
        
        Returns:
            Словарь со статистикой
        """
        logs = self._read_log()
        
        total = len(logs)
        pending = sum(1 for log in logs if log.get("status") == "pending_review")
        approved = sum(1 for log in logs if log.get("status") == "approved")
        rejected = sum(1 for log in logs if log.get("status") == "rejected")
        
        return {
            "total": total,
            "pending_review": pending,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round((approved / total * 100) if total > 0 else 0, 2)
        }
