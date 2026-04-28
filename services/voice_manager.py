"""
Сервис управления голосовыми предпочтениями пользователей и кэширования TTS
"""
import os
import json
import hashlib
from typing import Optional
from datetime import datetime, timezone
import logging
import fcntl

logger = logging.getLogger("service_desk")

USER_PREFERENCES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user_preferences.json")
TTS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "tts_cache")


class VoicePreferencesManager:
    """Управление голосовыми настройками пользователей"""

    def __init__(self, preferences_path: str = None):
        self.preferences_path = preferences_path or USER_PREFERENCES_PATH
        os.makedirs(os.path.dirname(self.preferences_path), exist_ok=True)
        
        # Инициализируем файл если не существует
        if not os.path.exists(self.preferences_path):
            self._initialize_preferences_file()
        
        logger.info(f"VoicePreferencesManager инициализирован: {self.preferences_path}")

    def _initialize_preferences_file(self):
        """Инициализирует файл настроек пустым объектом"""
        with open(self.preferences_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    def _read_preferences(self) -> dict:
        """Читает настройки с блокировкой файла"""
        try:
            with open(self.preferences_path, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    # json.load автоматически использует последнее значение при дубликатах ключей
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Файл настроек поврежден, создаю новый")
            self._initialize_preferences_file()
            return {}

    def _write_preferences(self, data: dict):
        """Записывает настройки с эксклюзивной блокировкой"""
        try:
            # Очищаем данные от возможных дубликатов (на всякий случай)
            clean_data = {}
            for key, value in data.items():
                clean_data[key] = value
            
            # Записываем напрямую с усечением файла
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(clean_data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                    # Усекаем файл до текущей позиции (на случай если новый контент короче)
                    f.truncate()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            logger.debug(f"Настройки сохранены: {len(clean_data)} пользователей")
        except Exception as e:
            logger.error(f"Ошибка записи настроек: {e}", exc_info=True)
            raise

    def get_user_voice_preference(self, user_id: str) -> bool:
        """
        Получает предпочтение пользователя по озвучке
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если озвучка включена (по умолчанию True)
        """
        prefs = self._read_preferences()
        user_prefs = prefs.get(user_id, {})
        
        # По умолчанию озвучка включена
        return user_prefs.get("voice_enabled", True)

    def set_user_voice_preference(self, user_id: str, enabled: bool) -> bool:
        """
        Устанавливает предпочтение пользователя по озвучке
        
        Args:
            user_id: ID пользователя
            enabled: Включить (True) или выключить (False) озвучку
            
        Returns:
            True если успешно обновлено
        """
        prefs = self._read_preferences()
        
        if user_id not in prefs:
            prefs[user_id] = {}
        
        prefs[user_id]["voice_enabled"] = enabled
        prefs[user_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self._write_preferences(prefs)
        logger.info(f"Настройка озвучки для {user_id}: {'включена' if enabled else 'выключена'}")
        return True

    def toggle_user_voice(self, user_id: str) -> bool:
        """
        Переключает состояние озвучки для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Новое состояние (True/False)
        """
        current = self.get_user_voice_preference(user_id)
        new_state = not current
        self.set_user_voice_preference(user_id, new_state)
        return new_state


class TTSCacheManager:
    """Кэширование сгенерированных аудиофайлов TTS"""

    def __init__(self, cache_dir: str = None, max_cache_size_mb: int = 100):
        self.cache_dir = cache_dir or TTS_CACHE_DIR
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"TTSCacheManager инициализирован: {self.cache_dir}")

    def _get_cache_key(self, text: str, voice: str = "alena", lang: str = "ru-RU") -> str:
        """
        Генерирует ключ кэша на основе текста и параметров голоса
        
        Args:
            text: Текст для озвучивания
            voice: Голос
            lang: Язык
            
        Returns:
            Хэш-ключ для кэша
        """
        cache_string = f"{text}|{voice}|{lang}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()

    def get_cached_audio(self, text: str, voice: str = "alena", lang: str = "ru-RU") -> Optional[str]:
        """
        Проверяет наличие аудио в кэше
        
        Args:
            text: Текст для озвучивания
            voice: Голос
            lang: Язык
            
        Returns:
            Путь к кэшированному файлу или None
        """
        cache_key = self._get_cache_key(text, voice, lang)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.ogg")
        
        if os.path.exists(cache_path):
            logger.debug(f"TTS кэш hit для текста: {text[:50]}...")
            return cache_path
        
        return None

    def cache_audio(self, text: str, audio_path: str, voice: str = "alena", lang: str = "ru-RU") -> str:
        """
        Сохраняет аудио в кэш
        
        Args:
            text: Текст для озвучивания
            audio_path: Путь к сгенерированному аудио
            voice: Голос
            lang: Язык
            
        Returns:
            Путь к кэшированному файлу
        """
        cache_key = self._get_cache_key(text, voice, lang)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.ogg")
        
        try:
            # Копируем файл в кэш
            import shutil
            shutil.copy2(audio_path, cache_path)
            
            # Проверяем размер кэша и очищаем если нужно
            self._cleanup_cache_if_needed()
            
            logger.debug(f"TTS кэширован: {cache_path}")
            return cache_path
        except Exception as e:
            logger.error(f"Ошибка кэширования TTS: {e}")
            return audio_path  # Возвращаем оригинальный путь при ошибке

    def _cleanup_cache_if_needed(self):
        """Очищает кэш если превышен максимальный размер"""
        try:
            # Вычисляем общий размер кэша
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f))
                for f in os.listdir(self.cache_dir)
                if os.path.isfile(os.path.join(self.cache_dir, f))
            )
            
            # Если превышен лимит, удаляем старые файлы
            if total_size > self.max_cache_size_bytes:
                logger.info(f"Очистка TTS кэша: {total_size / (1024*1024):.2f} MB > {self.max_cache_size_bytes / (1024*1024)} MB")
                
                # Получаем список файлов с временем создания
                files = [
                    (os.path.join(self.cache_dir, f), os.path.getctime(os.path.join(self.cache_dir, f)))
                    for f in os.listdir(self.cache_dir)
                    if os.path.isfile(os.path.join(self.cache_dir, f))
                ]
                
                # Сортируем по времени (старые первые)
                files.sort(key=lambda x: x[1])
                
                # Удаляем файлы пока не освободим достаточно места
                for file_path, _ in files:
                    if total_size <= self.max_cache_size_bytes * 0.8:  # Очищаем до 80% от лимита
                        break
                    os.remove(file_path)
                    total_size -= os.path.getsize(file_path)
                
                logger.info(f"TTS кэш очищен, новый размер: {total_size / (1024*1024):.2f} MB")
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")

    def clear_cache(self):
        """Полностью очищает кэш"""
        try:
            for f in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("TTS кэш полностью очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")

    def get_cache_stats(self) -> dict:
        """
        Получает статистику кэша
        
        Returns:
            Словарь со статистикой
        """
        try:
            files = [f for f in os.listdir(self.cache_dir) if os.path.isfile(os.path.join(self.cache_dir, f))]
            total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in files)
            
            return {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_size_mb": self.max_cache_size_bytes / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {"file_count": 0, "total_size_bytes": 0, "total_size_mb": 0}
