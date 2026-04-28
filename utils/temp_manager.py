"""
Утилиты для управления временными файлами
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TEMP_DIR = "./temp"
MAX_FILE_AGE_SECONDS = 3600  # 1 час
MAX_DIR_SIZE_MB = 500  # Максимальный размер директории в MB


def cleanup_old_files(max_age_seconds: int = MAX_FILE_AGE_SECONDS) -> int:
    """
    Удаляет файлы старше указанного времени
    
    Args:
        max_age_seconds: Максимальный возраст файла в секундах
        
    Returns:
        Количество удаленных файлов
    """
    if not os.path.exists(TEMP_DIR):
        return 0
    
    current_time = time.time()
    removed_count = 0
    
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Пропускаем директории
        if os.path.isdir(filepath):
            continue
        
        try:
            file_age = current_time - os.path.getmtime(filepath)
            
            if file_age > max_age_seconds:
                os.remove(filepath)
                removed_count += 1
                logger.debug(f"Удален старый файл: {filename} (возраст: {file_age:.0f}s)")
        except Exception as e:
            logger.error(f"Ошибка удаления файла {filename}: {e}")
    
    if removed_count > 0:
        logger.info(f"Очистка temp: удалено {removed_count} файлов")
    
    return removed_count


def get_dir_size_mb(path: str = TEMP_DIR) -> float:
    """
    Вычисляет размер директории в MB
    
    Args:
        path: Путь к директории
        
    Returns:
        Размер в MB
    """
    if not os.path.exists(path):
        return 0.0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                continue
    
    return total_size / (1024 * 1024)


def enforce_size_limit(max_size_mb: float = MAX_DIR_SIZE_MB) -> int:
    """
    Удаляет самые старые файлы, если размер директории превышает лимит
    
    Args:
        max_size_mb: Максимальный размер в MB
        
    Returns:
        Количество удаленных файлов
    """
    if not os.path.exists(TEMP_DIR):
        return 0
    
    current_size = get_dir_size_mb()
    
    if current_size <= max_size_mb:
        return 0
    
    logger.warning(f"Размер temp директории ({current_size:.1f}MB) превышает лимит ({max_size_mb}MB)")
    
    # Получаем список файлов с временем модификации
    files_with_age = []
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(filepath):
            try:
                mtime = os.path.getmtime(filepath)
                size = os.path.getsize(filepath)
                files_with_age.append((filepath, mtime, size))
            except OSError:
                continue
    
    # Сортируем по времени (самые старые первые)
    files_with_age.sort(key=lambda x: x[1])
    
    removed_count = 0
    for filepath, mtime, size in files_with_age:
        if get_dir_size_mb() <= max_size_mb:
            break
        
        try:
            os.remove(filepath)
            removed_count += 1
            logger.debug(f"Удален файл для освобождения места: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Ошибка удаления файла {filepath}: {e}")
    
    if removed_count > 0:
        new_size = get_dir_size_mb()
        logger.info(f"Очистка по размеру: удалено {removed_count} файлов, новый размер: {new_size:.1f}MB")
    
    return removed_count


def cleanup_temp(max_age_seconds: int = MAX_FILE_AGE_SECONDS, 
                 max_size_mb: float = MAX_DIR_SIZE_MB) -> dict:
    """
    Полная очистка временных файлов
    
    Args:
        max_age_seconds: Максимальный возраст файла
        max_size_mb: Максимальный размер директории
        
    Returns:
        Статистика очистки
    """
    initial_size = get_dir_size_mb()
    
    # Сначала удаляем старые файлы
    old_removed = cleanup_old_files(max_age_seconds)
    
    # Затем проверяем лимит размера
    size_removed = enforce_size_limit(max_size_mb)
    
    final_size = get_dir_size_mb()
    
    result = {
        "old_files_removed": old_removed,
        "size_limit_files_removed": size_removed,
        "total_removed": old_removed + size_removed,
        "initial_size_mb": round(initial_size, 2),
        "final_size_mb": round(final_size, 2),
        "freed_mb": round(initial_size - final_size, 2)
    }
    
    logger.info(f"Очистка temp завершена: {result}")
    return result


def schedule_periodic_cleanup(interval_seconds: int = 1800):
    """
    Запускает периодическую очистку в фоновом потоке
    
    Args:
        interval_seconds: Интервал между очистками (по умолчанию 30 минут)
    """
    import threading
    
    def cleanup_loop():
        while True:
            time.sleep(interval_seconds)
            try:
                cleanup_temp()
            except Exception as e:
                logger.error(f"Ошибка периодической очистки: {e}")
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info(f"Запущена периодическая очистка temp (интервал: {interval_seconds}s)")
