#!/usr/bin/env python3
"""
Утилита для просмотра и управления неразрешенными вопросами
Использование: python manage_unanswered.py [command] [options]

Команды:
  list          - Показать список вопросов на рассмотрении
  stats         - Показать статистику
  approve ID    - Подтвердить ответ для записи с указанным ID
  reject ID     - Отклонить запись с указанным ID
"""
import sys
import os
import json

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.unanswered_logger import UnansweredQuestionsLogger


def print_list(logger: UnansweredQuestionsLogger, limit=10):
    """Выводит список вопросов на рассмотрении"""
    questions = logger.get_pending_questions(limit=limit)
    
    if not questions:
        print("✅ Нет вопросов на рассмотрении")
        return
    
    print(f"\n📋 Вопросы на рассмотрении ({len(questions)} шт.):\n")
    print("=" * 80)
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. ID: {q['id'][:8]}...")
        print(f"   Вопрос: {q['question'][:100]}")
        print(f"   Пользователь: {q['user_id']}")
        print(f"   Дата: {q['created_at'][:19]}")
        
        if q.get('suggested_answer'):
            print(f"   Черновик ответа: {q['suggested_answer'][:100]}")
        
        if q.get('has_image'):
            print(f"   ⚠️  Содержит изображение")
        
        print("-" * 80)
    
    print(f"\n💡 Для подтверждения ответа используйте: python manage_unanswered.py approve <ID>")
    print(f"   Для отклонения: python manage_unanswered.py reject <ID>\n")


def print_stats(logger: UnansweredQuestionsLogger):
    """Выводит статистику"""
    stats = logger.get_statistics()
    
    print("\n📊 Статистика неразрешенных вопросов:\n")
    print(f"   Всего вопросов: {stats['total']}")
    print(f"   На рассмотрении: {stats['pending_review']}")
    print(f"   Подтверждено: {stats['approved']}")
    print(f"   Отклонено: {stats['rejected']}")
    print(f"   Процент одобрения: {stats['approval_rate']}%\n")


def approve_answer(logger: UnansweredQuestionsLogger, record_id: str):
    """Подтверждает ответ"""
    # В реальном приложении здесь был бы интерактивный ввод ответа
    print(f"\n⚠️  Функция подтверждения требует доработки админ-интерфейса")
    print(f"   Запись ID: {record_id}")
    print(f"   Статус изменится на 'approved' после добавления финального ответа\n")


def reject_question(logger: UnansweredQuestionsLogger, record_id: str):
    """Отклоняет вопрос"""
    success = logger.reject_question(record_id, reason="Отклонено через CLI")
    if success:
        print(f"✅ Запись {record_id[:8]}... отклонена")
    else:
        print(f"❌ Ошибка: запись {record_id} не найдена")


def main():
    logger = UnansweredQuestionsLogger()
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print_list(logger, limit)
    
    elif command == "stats":
        print_stats(logger)
    
    elif command == "approve":
        if len(sys.argv) < 3:
            print("❌ Укажите ID записи: python manage_unanswered.py approve <ID>")
            sys.exit(1)
        approve_answer(logger, sys.argv[2])
    
    elif command == "reject":
        if len(sys.argv) < 3:
            print("❌ Укажите ID записи: python manage_unanswered.py reject <ID>")
            sys.exit(1)
        reject_question(logger, sys.argv[2])
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
