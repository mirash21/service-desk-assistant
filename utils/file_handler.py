"""
Утилиты для работы с файлами
"""
import aiohttp
import aiofiles
import os
from utils.logger import logger

# Try to import config, fallback to defaults if not available
try:
    from config import TEMP_DIR, MAX_FILE_SIZE
except ImportError:
    TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB default


async def download_file(url: str, headers: dict, file_type: str = "bin") -> str:
    """
    Асинхронная загрузка файла с проверкой размера

    Args:
        url: URL файла
        headers: HTTP заголовки для авторизации
        file_type: Расширение файла

    Returns:
        Путь к загруженному файлу
        
    Raises:
        Exception: Если файл превышает максимальный размер
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Ошибка загрузки файла: {resp.status}")

            # Проверка размера файла
            content_length = resp.headers.get('Content-Length')
            if content_length and int(content_length) > MAX_FILE_SIZE:
                raise Exception(f"Файл слишком большой: {int(content_length) / 1024 / 1024:.2f} MB (максимум {MAX_FILE_SIZE / 1024 / 1024:.2f} MB)")

            content = await resp.read()
            
            # Дополнительная проверка после загрузки
            if len(content) > MAX_FILE_SIZE:
                raise Exception(f"Загруженный файл слишком большой: {len(content) / 1024 / 1024:.2f} MB")

    # Используем временное имя файла с timestamp
    import time
    file_id = f"{int(time.time() * 1000)}"
    file_path = os.path.join(TEMP_DIR, f"{file_id}.{file_type}")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(f"Файл загружен: {file_path} ({len(content)} байт)")
    return file_path


def cleanup_temp_files():
    """Очистка временных файлов"""
    if os.path.exists(TEMP_DIR):
        cleaned = 0
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    cleaned += 1
            except Exception as e:
                logger.error(f"Ошибка удаления {file_path}: {e}")
        logger.info(f"Очищено временных файлов: {cleaned}")
