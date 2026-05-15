"""
Система аудита действий пользователей для соответствия 152-ФЗ.

Регистрирует все операции с персональными данными, обеспечивая
полную прослеживаемость и подотчетность.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class AuditLogger:
    """Класс для логирования аудиторских событий."""
    
    def __init__(self, log_dir: str = "data/audit_logs"):
        """
        Инициализация аудитора.
        
        Args:
            log_dir: Директория для хранения логов аудита
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # File handler для аудита
        audit_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(audit_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Форматирование
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
    
    def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """
        Регистрация аудиторского события.
        
        Args:
            event_type: Тип события (ACCESS, MODIFY, DELETE, EXPORT, etc.)
            user_id: ID пользователя
            action: Выполненное действие
            resource: Ресурс, над которым выполнено действие
            details: Дополнительные детали
            ip_address: IP адрес
            success: Успешность операции
        """
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'ip_address': ip_address or 'unknown',
        }
        
        if details:
            # Маскируем чувствительные данные в деталях
            from utils.pii_masker import pii_masker
            audit_record['details'] = pii_masker.mask_dict(details)
        
        # Запись в лог
        self.logger.info(json.dumps(audit_record, ensure_ascii=False))
    
    def log_data_access(self, user_id: str, data_type: str, record_count: int = 1, **kwargs):
        """Логирование доступа к данным."""
        self.log_event(
            event_type='DATA_ACCESS',
            user_id=user_id,
            action='access',
            resource=data_type,
            details={'record_count': record_count, **kwargs}
        )
    
    def log_data_export(self, user_id: str, export_format: str, record_count: int, **kwargs):
        """Логирование экспорта данных."""
        self.log_event(
            event_type='DATA_EXPORT',
            user_id=user_id,
            action='export',
            resource=f'{export_format}_export',
            details={'record_count': record_count, **kwargs}
        )
    
    def log_data_modification(self, user_id: str, resource: str, changes: Dict, **kwargs):
        """Логирование изменения данных."""
        self.log_event(
            event_type='DATA_MODIFICATION',
            user_id=user_id,
            action='modify',
            resource=resource,
            details={'changes': changes, **kwargs}
        )
    
    def log_data_deletion(self, user_id: str, resource: str, record_id: str, **kwargs):
        """Логирование удаления данных."""
        self.log_event(
            event_type='DATA_DELETION',
            user_id=user_id,
            action='delete',
            resource=resource,
            details={'record_id': record_id, **kwargs}
        )
    
    def log_consent_change(self, user_id: str, consent_type: str, granted: bool, **kwargs):
        """Логирование изменения согласий."""
        self.log_event(
            event_type='CONSENT_CHANGE',
            user_id=user_id,
            action='consent_update',
            resource=consent_type,
            details={'granted': granted, **kwargs}
        )
    
    def log_authentication(self, user_id: str, method: str, success: bool, **kwargs):
        """Логирование аутентификации."""
        self.log_event(
            event_type='AUTHENTICATION',
            user_id=user_id,
            action='login',
            resource=method,
            success=success,
            details=kwargs
        )
    
    def log_admin_action(self, user_id: str, action: str, resource: str, **kwargs):
        """Логирование административных действий."""
        self.log_event(
            event_type='ADMIN_ACTION',
            user_id=user_id,
            action=action,
            resource=resource,
            details=kwargs
        )


# Глобальный экземпляр
audit_logger = AuditLogger()
