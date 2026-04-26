"""
Конфигурация проекта Service Desk Assistant
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# MAX Messenger
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
MAX_API_URL = "https://platform-api.max.ru"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Yandex AI Studio
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://supabase-api.vaib-cod.ru")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Модели
YANDEX_GPT_MODEL = "yandexgpt/latest"
YANDEX_EMBEDDING_MODEL = "text-search-doc/latest"

# Настройки
TEMP_DIR = "./temp"
DATA_DIR = "./data"
LOGS_DIR = "./logs"

# Максимальный размер файла (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_config():
    """Валидация обязательных параметров конфигурации"""
    errors = []
    
    if not MAX_BOT_TOKEN or MAX_BOT_TOKEN == "your_max_bot_token_here":
        errors.append("MAX_BOT_TOKEN не настроен в .env файле")
    
    if not YANDEX_API_KEY or YANDEX_API_KEY == "your_yandex_api_key_here":
        errors.append("YANDEX_API_KEY не настроен в .env файле")
    
    if not SUPABASE_KEY or SUPABASE_KEY == "your_supabase_anon_key_here":
        errors.append("SUPABASE_KEY не настроен в .env файле")
    
    if errors:
        print("❌ Ошибки конфигурации:")
        for error in errors:
            print(f"  - {error}")
        print("\nСкопируйте .env.example в .env и заполните необходимые параметры")
        sys.exit(1)
    
    return True
