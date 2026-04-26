"""
Скрипт для проверки работоспособности системы
"""
import sys
from config import validate_config, SUPABASE_URL, YANDEX_API_KEY
from utils.logger import logger
from services.yandex_service import YandexAIService
from rag.supabase_manager import SupabaseRAGManager


def check_configuration():
    """Проверка конфигурации"""
    logger.info("📝 Проверка конфигурации...")
    try:
        validate_config()
        logger.info("✅ Конфигурация валидна")
        return True
    except SystemExit:
        logger.error("❌ Ошибка конфигурации")
        return False


def check_yandex_api():
    """Проверка подключения к Yandex API"""
    logger.info("☁️  Проверка Yandex AI Studio...")
    try:
        service = YandexAIService()
        
        # Тест генерации текста
        response = service.generate_text(
            "Привет! Это тестовое сообщение.",
            temperature=0.1
        )
        
        if response:
            logger.info(f"✅ YandexGPT работает (ответ: {len(response)} символов)")
            return True
        else:
            logger.error("❌ YandexGPT не вернул ответ")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Yandex API: {e}")
        return False


def check_supabase():
    """Проверка подключения к Supabase"""
    logger.info("🗄️  Проверка Supabase...")
    try:
        manager = SupabaseRAGManager()
        stats = manager.get_stats()
        
        logger.info(f"✅ Supabase подключен")
        logger.info(f"   - Документов: {stats['total_docs']}")
        logger.info(f"   - URL: {SUPABASE_URL}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Supabase: {e}")
        return False


def check_directories():
    """Проверка директорий"""
    logger.info("📁 Проверка директорий...")
    import os
    from config import TEMP_DIR, DATA_DIR, LOGS_DIR
    
    directories = [TEMP_DIR, DATA_DIR, LOGS_DIR]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"✅ Директория {dir_path} создана/существует")
    
    return True


def main():
    """Запуск всех проверок"""
    logger.info("=" * 60)
    logger.info("🔍 Проверка работоспособности системы")
    logger.info("=" * 60)
    
    checks = [
        ("Конфигурация", check_configuration),
        ("Директории", check_directories),
        ("Yandex API", check_yandex_api),
        ("Supabase", check_supabase),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Проверка '{name}' упала с ошибкой: {e}")
            results.append((name, False))
    
    # Итоговый отчет
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("✅ Все проверки пройдены успешно!")
        logger.info("🚀 Система готова к запуску")
        return 0
    else:
        logger.error("❌ Некоторые проверки не пройдены")
        logger.info("🔧 Исправьте ошибки и повторите проверку")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
