#!/usr/bin/env python3
"""
Анализатор неразрешенных вопросов
Выявляет паттерны в вопросах без ответов и предлагает дополнить базу знаний
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = os.getenv('DATA_DIR', 'data')
UNANSWERED_FILE = os.path.join(DATA_DIR, 'unanswered_questions.json')


def load_unanswered_questions():
    """Загрузка неразрешенных вопросов"""
    if not os.path.exists(UNANSWERED_FILE):
        print(f"❌ Файл {UNANSWERED_FILE} не найден")
        return []
    
    with open(UNANSWERED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('unanswered_questions', [])


def analyze_patterns(questions):
    """Анализ паттернов в неразрешенных вопросах"""
    
    print("=" * 70)
    print("АНАЛИЗ НЕРАЗРЕШЕННЫХ ВОПРОСОВ")
    print("=" * 70)
    print(f"\n📊 Всего неразрешенных вопросов: {len(questions)}\n")
    
    if not questions:
        print("✅ Нет неразрешенных вопросов!")
        return
    
    # 1. Анализ по времени
    print("📅 Распределение по времени:")
    time_groups = defaultdict(int)
    for q in questions:
        timestamp = q.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = dt.strftime('%Y-%m-%d')
                time_groups[date_key] += 1
            except:
                pass
    
    # Показываем последние 7 дней
    sorted_dates = sorted(time_groups.keys(), reverse=True)[:7]
    for date in sorted_dates:
        count = time_groups[date]
        bar = "█" * count
        print(f"   {date}: {count:3d} {bar}")
    
    # 2. Топ частых вопросов (похожие формулировки)
    print(f"\n🔝 Топ-10 наиболее частых вопросов:")
    question_counts = Counter()
    for q in questions:
        # Нормализуем вопрос (убираем пунктуацию, приводим к нижнему регистру)
        text = q.get('question', '').lower()
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        # Группируем по ключевым словам (первые 5 слов)
        words = text.split()[:5]
        key = ' '.join(words)
        if len(key) > 10:  # Игнорируем слишком короткие
            question_counts[key] += 1
    
    for question_key, count in question_counts.most_common(10):
        print(f"   {count:3d}x: {question_key}...")
    
    # 3. Анализ по режимам
    print(f"\n🎯 Распределение по режимам:")
    mode_counts = Counter(q.get('mode', 'unknown') for q in questions)
    for mode, count in mode_counts.most_common():
        percentage = (count / len(questions)) * 100
        print(f"   {mode:15s}: {count:4d} ({percentage:5.1f}%)")
    
    # 4. Вопросы с изображениями vs текст
    print(f"\n🖼️  Типы вопросов:")
    with_image = sum(1 for q in questions if q.get('has_image', False))
    without_image = len(questions) - with_image
    print(f"   С изображениями: {with_image:4d} ({with_image/len(questions)*100:.1f}%)")
    print(f"   Только текст:    {without_image:4d} ({without_image/len(questions)*100:.1f}%)")
    
    # 5. Кластеризация по темам (простая - по ключевым словам)
    print(f"\n📚 Тематические кластеры:")
    topic_keywords = {
        'Принтеры': ['принтер', 'печать', 'картридж', 'сканер'],
        'Сеть': ['сеть', 'интернет', 'wi-fi', 'wifi', 'подключение'],
        'Почта': ['почта', 'email', 'outlook', 'письмо'],
        'Пароли': ['пароль', 'password', 'сброс', 'доступ'],
        'Программы': ['программа', 'software', 'установить', 'обновить'],
        'Windows': ['windows', 'система', 'компьютер', 'перезагруз'],
        'VPN': ['vpn', 'удален', 'remote'],
        'Телефония': ['телефон', 'звонок', 'гарнитур'],
    }
    
    topic_counts = defaultdict(list)
    for q in questions:
        question_lower = q.get('question', '').lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                topic_counts[topic].append(q['question'])
                break  # Только одна тема на вопрос
    
    for topic, qs in sorted(topic_counts.items(), key=lambda x: len(x[1]), reverse=True):
        if len(qs) >= 2:  # Показываем только темы с 2+ вопросами
            print(f"\n   📌 {topic} ({len(qs)} вопросов):")
            for q in qs[:3]:  # Первые 3 примера
                print(f"      - {q[:80]}...")
            if len(qs) > 3:
                print(f"      ... и еще {len(qs) - 3}")
    
    # 6. Рекомендации по дополнению базы знаний
    print(f"\n💡 РЕКОМЕНДАЦИИ ПО ДОПОЛНЕНИЮ БАЗЫ ЗНАНИЙ:\n")
    
    recommendations = []
    
    # Темы с большим количеством вопросов
    for topic, qs in sorted(topic_counts.items(), key=lambda x: len(x[1]), reverse=True):
        if len(qs) >= 3:
            recommendations.append({
                'priority': 'HIGH',
                'topic': topic,
                'count': len(qs),
                'examples': qs[:2],
                'action': f"Добавить 5-10 Q&A по теме '{topic}'"
            })
    
    # Частые вопросы
    for question_key, count in question_counts.most_common(5):
        if count >= 3:
            # Находим полный пример вопроса
            example_q = next((q['question'] for q in questions 
                            if question_key.replace(' ', '') in q['question'].lower().replace(' ', '')), 
                           question_key)
            recommendations.append({
                'priority': 'HIGH' if count >= 5 else 'MEDIUM',
                'topic': 'Частый вопрос',
                'count': count,
                'examples': [example_q],
                'action': f"Добавить конкретный ответ на часто задаваемый вопрос"
            })
    
    # Вопросы с изображениями
    if with_image > len(questions) * 0.3:
        recommendations.append({
            'priority': 'MEDIUM',
            'topic': 'Изображения',
            'count': with_image,
            'examples': [],
            'action': "Улучшить распознавание изображений или добавить больше визуальных примеров в базу"
        })
    
    # Сортируем по приоритету
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    for i, rec in enumerate(recommendations[:10], 1):
        print(f"{i}. [{rec['priority']}] {rec['action']}")
        print(f"   Примеры: {rec['examples'][0][:100] if rec['examples'] else 'N/A'}")
        print(f"   Количество вопросов: {rec['count']}\n")
    
    return recommendations


def generate_knowledge_suggestions(recommendations):
    """Генерация предложений для новых Q&A"""
    
    if not recommendations:
        return
    
    print("\n" + "=" * 70)
    print("ПРЕДЛОЖЕНИЯ ДЛЯ НОВЫХ Q&A В БАЗУ ЗНАНИЙ")
    print("=" * 70)
    
    output_file = os.path.join(DATA_DIR, 'suggested_qa.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Предложения для дополнения базы знаний RAG\n")
        f.write(f"# Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, rec in enumerate(recommendations[:5], 1):
            f.write(f"## {i}. Тема: {rec['topic']} (Приоритет: {rec['priority']})\n\n")
            f.write(f"Количество похожих вопросов: {rec['count']}\n\n")
            
            if rec['examples']:
                f.write("Примеры вопросов пользователей:\n")
                for example in rec['examples'][:3]:
                    f.write(f"- {example}\n")
                f.write("\n")
            
            f.write(f"Рекомендация: {rec['action']}\n\n")
            f.write("Пример формата для добавления:\n")
            f.write("```python\n")
            f.write(f"(\"В: [вопрос по теме {rec['topic']}]\", \"О: [подробный ответ]\"),\n")
            f.write("```\n\n")
            f.write("-" * 70 + "\n\n")
    
    print(f"\n✅ Предложения сохранены в: {output_file}")
    print(f"   Используйте этот файл как основу для расширения базы знаний")


def export_to_csv(questions):
    """Экспорт в CSV для детального анализа"""
    
    import csv
    
    output_file = os.path.join(DATA_DIR, 'unanswered_questions_export.csv')
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Question', 'Mode', 'Has Image', 'User ID', 'Suggested Answer'])
        
        for q in questions:
            writer.writerow([
                q.get('timestamp', ''),
                q.get('question', ''),
                q.get('mode', ''),
                q.get('has_image', False),
                q.get('user_id', ''),
                q.get('suggested_answer', '')[:200]  # Ограничиваем длину
            ])
    
    print(f"\n📄 Детальный экспорт сохранен в: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ неразрешенных вопросов RAG')
    parser.add_argument('--export', action='store_true', help='Экспорт в CSV')
    parser.add_argument('--generate', action='store_true', help='Генерация предложений Q&A')
    
    args = parser.parse_args()
    
    # Загрузка вопросов
    questions = load_unanswered_questions()
    
    if not questions:
        print("Нет данных для анализа")
        sys.exit(0)
    
    # Анализ
    recommendations = analyze_patterns(questions)
    
    # Экспорт если запрошено
    if args.export:
        export_to_csv(questions)
    
    # Генерация предложений если запрошено
    if args.generate and recommendations:
        generate_knowledge_suggestions(recommendations)
    
    print("\n" + "=" * 70)
    print("Анализ завершен!")
    print("=" * 70)
