"""
Модуль маскирования персональных данных (PII) для соответствия 152-ФЗ.

Обеспечивает автоматическое маскирование чувствительных данных в логах
и выводах приложения.
"""

import re
from typing import Any, Dict, Optional


class PIIMasker:
    """Класс для маскирования персональных данных."""
    
    # Паттерны для обнаружения PII
    PATTERNS = {
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        'phone_ru': re.compile(r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),
        'passport': re.compile(r'\b\d{4}[\s\-]?\d{6}\b'),
        'snils': re.compile(r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b'),
        'inn': re.compile(r'\b\d{10,12}\b'),
        'credit_card': re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
    }
    
    @classmethod
    def mask_email(cls, text: str) -> str:
        """Маскирует email адреса."""
        def replace_email(match):
            email = match.group(0)
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                masked_username = username[0] + '***' if len(username) > 1 else '***'
                return f"{masked_username}@{domain}"
            return '***@***.***'
        
        return cls.PATTERNS['email'].sub(replace_email, text)
    
    @classmethod
    def mask_phone(cls, text: str) -> str:
        """Маскирует номера телефонов."""
        return cls.PATTERNS['phone_ru'].sub('+7 (***) ***-**-**', text)
    
    @classmethod
    def mask_passport(cls, text: str) -> str:
        """Маскирует паспортные данные."""
        return cls.PATTERNS['passport'].sub('**** ******', text)
    
    @classmethod
    def mask_snils(cls, text: str) -> str:
        """Маскирует СНИЛС."""
        return cls.PATTERNS['snils'].sub('***-***-*** **', text)
    
    @classmethod
    def mask_inn(cls, text: str) -> str:
        """Маскирует ИНН."""
        def replace_inn(match):
            inn = match.group(0)
            return '*' * (len(inn) - 4) + inn[-4:]
        
        return cls.PATTERNS['inn'].sub(replace_inn, text)
    
    @classmethod
    def mask_credit_card(cls, text: str) -> str:
        """Маскирует номера кредитных карт."""
        return cls.PATTERNS['credit_card'].sub('**** **** **** ****', text)
    
    @classmethod
    def mask_all(cls, text: str) -> str:
        """Применяет все маскирования к тексту."""
        if not isinstance(text, str):
            return str(text)
        
        # Порядок важен: сначала более специфичные паттерны
        text = cls.mask_credit_card(text)
        text = cls.mask_passport(text)
        text = cls.mask_snils(text)
        text = cls.mask_inn(text)
        text = cls.mask_phone(text)
        text = cls.mask_email(text)
        
        return text
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any], sensitive_keys: Optional[list] = None) -> Dict[str, Any]:
        """Маскирует чувствительные поля в словаре."""
        if sensitive_keys is None:
            sensitive_keys = [
                'email', 'phone', 'passport', 'snils', 'inn', 
                'credit_card', 'password', 'token', 'secret',
                'api_key', 'access_token'
            ]
        
        masked_data = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                if isinstance(value, str):
                    masked_data[key] = '***MASKED***'
                else:
                    masked_data[key] = value
            elif isinstance(value, dict):
                masked_data[key] = cls.mask_dict(value, sensitive_keys)
            elif isinstance(value, str):
                masked_data[key] = cls.mask_all(value)
            else:
                masked_data[key] = value
        
        return masked_data


# Глобальный экземпляр для удобства использования
pii_masker = PIIMasker()
