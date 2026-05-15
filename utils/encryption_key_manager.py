"""
Менеджер ключей шифрования для защиты персональных данных (152-ФЗ).

Обеспечивает безопасное хранение и управление ключами шифрования
для защиты чувствительных данных в базе данных.
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path


logger = logging.getLogger(__name__)


class EncryptionKeyManager:
    """Управление ключами шифрования."""
    
    def __init__(self, key_file: str = "data/encryption.key", master_password: str = None):
        """
        Инициализация менеджера ключей.
        
        Args:
            key_file: Путь к файлу ключа шифрования
            master_password: Мастер-пароль для генерации ключа
        """
        self.key_file = Path(key_file)
        self.master_password = master_password or os.getenv('ENCRYPTION_MASTER_PASSWORD')
        self._fernet = None
        
        # Создаем директорию если не существует
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Загружаем или создаем ключ
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Загружает существующий ключ или создает новый."""
        if self.key_file.exists():
            self._load_key()
        else:
            self._create_key()
    
    def _create_key(self):
        """Создает новый ключ шифрования."""
        if self.master_password:
            # Генерируем ключ из мастер-пароля
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
            
            # Сохраняем соль вместе с ключом
            with open(self.key_file, 'wb') as f:
                f.write(salt + key)
            
            logger.info("Ключ шифрования создан из мастер-пароля")
        else:
            # Генерируем случайный ключ
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            logger.info("Случайный ключ шифрования создан")
        
        self._load_key()
    
    def _load_key(self):
        """Загружает ключ шифрования из файла."""
        with open(self.key_file, 'rb') as f:
            key_data = f.read()
        
        # Проверяем, есть ли соль (ключ > 44 байт)
        if len(key_data) > 44:
            salt = key_data[:16]
            key = key_data[16:]
            
            if self.master_password:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=480000,
                )
                derived_key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
                self._fernet = Fernet(derived_key)
            else:
                self._fernet = Fernet(key)
        else:
            self._fernet = Fernet(key_data)
        
        logger.info("Ключ шифрования загружен")
    
    def encrypt(self, data: str) -> str:
        """
        Шифрует данные.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованные данные в base64
        """
        if not self._fernet:
            raise RuntimeError("Ключ шифрования не инициализирован")
        
        encrypted = self._fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Расшифровывает данные.
        
        Args:
            encrypted_data: Зашифрованные данные в base64
            
        Returns:
            Расшифрованные данные
        """
        if not self._fernet:
            raise RuntimeError("Ключ шифрования не инициализирован")
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка расшифровки: {e}")
            raise
    
    def rotate_key(self):
        """Ротирует ключ шифрования."""
        old_key_file = self.key_file.with_suffix('.key.old')
        
        # Сохраняем старый ключ
        if self.key_file.exists():
            import shutil
            shutil.copy2(self.key_file, old_key_file)
        
        # Создаем новый ключ
        self._create_key()
        
        logger.info("Ключ шифрования ротирован")
        return old_key_file
    
    @staticmethod
    def generate_secure_key() -> str:
        """Генерирует безопасный ключ для хранения в env."""
        return Fernet.generate_key().decode('utf-8')


# Глобальный экземпляр
encryption_manager = EncryptionKeyManager()
