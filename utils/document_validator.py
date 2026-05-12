#!/usr/bin/env python3
"""
Валидатор качества документов перед добавлением в базу знаний RAG

Проверяет новые документы на соответствие стандартам качества:
1. Формат Q&A
2. Наличие keywords в metadata
3. Оптимальная длина чанка (300-500 символов)
4. Наличие синонимов
5. Категоризация
6. Контекстуализация
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Результат валидации документа"""
    is_valid: bool
    score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    auto_fixes: Dict[str, str] = field(default_factory=dict)


# Словарь категорий и их keywords
CATEGORY_KEYWORDS = {
    'printers': ['принтер', 'печать', 'driver', 'драйвер', 'картридж', 'toner', 'MFP', 'МФУ', 'сканер'],
    'network': ['сеть', 'wi-fi', 'wifi', 'internet', 'интернет', 'router', 'роутер', 'подключение', 'vpn', 'proxy'],
    'email': ['почта', 'email', 'outlook', 'thunderbird', 'письмо', 'attachment', 'вложение', 'smtp', 'imap'],
    'password': ['пароль', 'password', 'pin', 'пин-код', 'сброс', 'reset', 'учетная запись', 'account', 'login'],
    'software': ['программа', 'software', 'установка', 'install', 'обновление', 'update', 'лицензия', 'license'],
    'hardware': ['компьютер', 'computer', 'ноутбук', 'laptop', 'монитор', 'keyboard', 'клавиатура', 'мышь', 'mouse'],
    'security': ['вирус', 'virus', 'антивирус', 'firewall', 'брандмауэр', 'безопасность', 'security', 'malware'],
    'windows': ['windows', 'ошибка', 'error', 'синий экран', 'bsod', 'обновление windows', 'reboot'],
    'office': ['word', 'excel', 'powerpoint', 'office', 'документ', 'таблица', 'презентация', 'spreadsheet'],
    'crm': ['crm', 'клиент', 'customer', 'сделка', 'deal', 'контрагент', 'contractor'],
    'mobile': ['телефон', 'phone', 'mobile', 'android', 'ios', 'смартфон', 'tablet', 'планшет'],
}

# Синонимы для常见ных терминов
COMMON_SYNONYMS = {
    'пароль': 'password, пин-код, PIN',
    'принтер': 'печатное устройство, МФУ, printer',
    'компьютер': 'ПК, workstation, computer',
    'ноутбук': 'laptop, портативный компьютер',
    'сеть': 'network, локальная сеть, LAN',
    'интернет': 'internet, глобальная сеть, WAN',
    'почта': 'email, electronic mail, электронная почта',
    'программа': 'software, приложение, application',
    'ошибка': 'error, сбой, malfunction',
    'подключение': 'connection, connect, linking',
}


class DocumentQualityValidator:
    """Валидатор качества документов для RAG"""
    
    def __init__(self):
        self.min_chunk_length = 200
        self.max_chunk_length = 600
        self.optimal_chunk_length = 400
    
    def validate_document(self, content: str, metadata: Optional[Dict] = None) -> ValidationResult:
        """
        Полная валидация документа
        
        Args:
            content: Текст документа
            metadata: Метаданные документа
            
        Returns:
            ValidationResult с оценкой и рекомендациями
        """
        result = ValidationResult(is_valid=True, score=100.0)
        metadata = metadata or {}
        
        # Проверка 1: Формат Q&A
        self._check_qa_format(content, result)
        
        # Проверка 2: Длина чанка
        self._check_chunk_length(content, result)
        
        # Проверка 3: Keywords в metadata
        self._check_keywords(metadata, content, result)
        
        # Проверка 4: Категория
        self._check_category(metadata, content, result)
        
        # Проверка 5: Синонимы
        self._check_synonyms(content, result)
        
        # Проверка 6: Контекстуализация
        self._check_contextualization(content, result)
        
        # Определение валидности
        if result.score < 60:
            result.is_valid = False
        
        return result
    
    def _check_qa_format(self, content: str, result: ValidationResult):
        """Проверка формата вопрос-ответ"""
        if not re.search(r'[ВвQq]:\s', content):
            result.issues.append("❌ Документ не в формате Q&A (отсутствует 'В:' или 'Q:')")
            result.suggestions.append(
                "Добавьте вопрос в начале: 'В: [ваш вопрос]\\nО: [ваш ответ]'"
            )
            result.score -= 25
        else:
            result.warnings.append("✅ Формат Q&A корректен")
    
    def _check_chunk_length(self, content: str, result: ValidationResult):
        """Проверка длины чанка"""
        length = len(content)
        
        if length > self.max_chunk_length:
            result.issues.append(f"❌ Чанк слишком длинный: {length} символов (максимум {self.max_chunk_length})")
            result.suggestions.append(
                f"Разбейте текст на несколько чанков по {self.optimal_chunk_length} символов"
            )
            result.score -= 20
        elif length < self.min_chunk_length:
            result.warnings.append(f"⚠️  Чанк короткий: {length} символов (минимум {self.min_chunk_length})")
            result.score -= 5
        else:
            result.warnings.append(f"✅ Оптимальная длина: {length} символов")
    
    def _check_keywords(self, metadata: Dict, content: str, result: ValidationResult):
        """Проверка наличия keywords"""
        keywords = metadata.get('keywords', [])
        
        if not keywords:
            # Автоматически извлекаем keywords
            extracted_keywords = self._extract_keywords(content)
            
            if extracted_keywords:
                result.auto_fixes['keywords'] = extracted_keywords
                result.warnings.append(f"⚠️  Keywords отсутствуют, но могут быть добавлены автоматически: {extracted_keywords[:5]}")
                result.suggestions.append("Используйте метод add_suggested_keywords() для автоматического добавления")
                result.score -= 15
            else:
                result.issues.append("❌ Keywords отсутствуют и не могут быть извлечены")
                result.suggestions.append("Добавьте keywords вручную в metadata")
                result.score -= 20
        else:
            result.warnings.append(f"✅ Keywords присутствуют: {len(keywords)} шт.")
    
    def _check_category(self, metadata: Dict, content: str, result: ValidationResult):
        """Проверка категории"""
        category = metadata.get('category', '')
        
        if not category or category == 'unknown':
            # Автоматически определяем категорию
            suggested_category = self._detect_category(content)
            
            if suggested_category:
                result.auto_fixes['category'] = suggested_category
                result.warnings.append(f"⚠️  Категория отсутствует, рекомендуемая: '{suggested_category}'")
                result.suggestions.append(f"Установите category='{suggested_category}' в metadata")
                result.score -= 10
            else:
                result.issues.append("❌ Категория отсутствует и не может быть определена")
                result.suggestions.append("Укажите category вручную (printers, network, email, и т.д.)")
                result.score -= 15
        else:
            result.warnings.append(f"✅ Категория установлена: '{category}'")
    
    def _check_synonyms(self, content: str, result: ValidationResult):
        """Проверка наличия синонимов"""
        has_synonyms = False
        
        for term, synonyms in COMMON_SYNONYMS.items():
            if term.lower() in content.lower():
                synonym_list = [s.strip() for s in synonyms.split(',')]
                for synonym in synonym_list:
                    if synonym.lower() in content.lower():
                        has_synonyms = True
                        break
        
        if not has_synonyms:
            # Предлагаем добавить синонимы
            found_terms = []
            for term in COMMON_SYNONYMS.keys():
                if term.lower() in content.lower():
                    found_terms.append(term)
            
            if found_terms:
                result.suggestions.append(
                    f"💡 Рекомендуется добавить синонимы для: {', '.join(found_terms[:3])}. "
                    f"Пример: '{found_terms[0]} ({COMMON_SYNONYMS[found_terms[0]]})'"
                )
                result.score -= 10
            else:
                result.warnings.append("ℹ️  Синонимы не требуются для этого контента")
        else:
            result.warnings.append("✅ Синонимы присутствуют")
    
    def _check_contextualization(self, content: str, result: ValidationResult):
        """Проверка контекстуализации"""
        lines = content.split('\n')
        
        # Проверяем наличие заголовка/контекста в начале
        if len(lines) > 1:
            first_line = lines[0].strip()
            
            # Если первая строка короткая и не начинается с В:/О:/•
            if (len(first_line) < 100 and 
                not first_line.startswith(('В:', 'О:', 'Q:', 'A:', '•', '1.', '-', '*'))):
                result.warnings.append("✅ Есть контекстный заголовок")
            else:
                result.suggestions.append(
                    "💡 Добавьте тематический заголовок в начало, например:\n"
                    "'Устранение неполадок принтера - Принтер не печатает:\\n'"
                )
                result.score -= 5
        else:
            result.suggestions.append(
                "💡 Добавьте контекстную информацию в начало документа"
            )
            result.score -= 5
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Извлекает keywords из контента"""
        content_lower = content.lower()
        keywords = []
        
        for category, category_keywords in CATEGORY_KEYWORDS.items():
            for keyword in category_keywords:
                if keyword.lower() in content_lower and keyword not in keywords:
                    keywords.append(keyword)
        
        # Добавляем общие keywords
        general_keywords = ['помощь', 'help', 'решение', 'solution', 'проблема', 'problem']
        for kw in general_keywords:
            if kw in content_lower and kw not in keywords:
                keywords.append(kw)
        
        return keywords[:10]
    
    def _detect_category(self, content: str) -> Optional[str]:
        """Определяет категорию на основе контента"""
        content_lower = content.lower()
        category_scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in content_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def add_suggested_keywords(self, metadata: Dict, content: str) -> Dict:
        """Добавляет предложенные keywords в metadata"""
        if 'keywords' not in metadata or not metadata['keywords']:
            metadata['keywords'] = self._extract_keywords(content)
        return metadata
    
    def add_suggested_category(self, metadata: Dict, content: str) -> Dict:
        """Добавляет предложенную категорию в metadata"""
        if not metadata.get('category') or metadata['category'] == 'unknown':
            category = self._detect_category(content)
            if category:
                metadata['category'] = category
        return metadata
    
    def suggest_synonyms_addition(self, content: str) -> str:
        """Предлагает добавить синонимы в текст"""
        improved_content = content
        
        for term, synonyms in COMMON_SYNONYMS.items():
            # Проверяем есть ли термин без синонимов
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, content, re.IGNORECASE):
                # Проверяем нет ли уже синонимов в скобках
                synonym_pattern = r'\b' + re.escape(term) + r'\s*\([^)]*' + re.escape(term) + r'[^)]*\)'
                if not re.search(synonym_pattern, content, re.IGNORECASE):
                    # Предлагаем замену
                    replacement = f"{term} ({synonyms})"
                    improved_content = re.sub(
                        pattern, 
                        replacement, 
                        improved_content, 
                        count=1,
                        flags=re.IGNORECASE
                    )
        
        return improved_content
    
    def split_long_chunk(self, content: str, target_size: int = 400, overlap: int = 50) -> List[str]:
        """Разбивает длинный чанк на несколько с перекрытием"""
        if len(content) <= self.max_chunk_length:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + target_size
            
            # Находим границу для разделения
            if end < len(content):
                # Сначала ищем конец предложения (точка, вопрос, восклицание)
                sentence_end = -1
                for punct in ['.', '?', '!', '\n']:
                    pos = content.rfind(punct, start, end)
                    if pos > start + 100:  # Минимальный размер чанка
                        if sentence_end == -1 or pos > sentence_end:
                            sentence_end = pos
                
                # Если нашли подходящую границу
                if sentence_end > start + 100:
                    end = sentence_end + 1
                else:
                    # Иначе ищем просто пробел или перенос строки
                    space_end = content.rfind(' ', start + 150, end)
                    if space_end > start:
                        end = space_end
            
            chunk = content[start:end].strip()
            if chunk and len(chunk) >= 100:
                chunks.append(chunk)
            
            # Перемещаемся с учетом перекрытия
            start = end - overlap if end > start + overlap else start + target_size
        
        return chunks
    
    def generate_validation_report(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Генерирует подробный отчет о валидации"""
        result = self.validate_document(content, metadata)
        
        report = []
        report.append("=" * 80)
        report.append("ОТЧЕТ ВАЛИДАЦИИ ДОКУМЕНТА")
        report.append("=" * 80)
        report.append(f"\nСтатус: {'✅ ПРОЙДЕН' if result.is_valid else '❌ НЕ ПРОЙДЕН'}")
        report.append(f"Оценка качества: {result.score:.0f}/100")
        report.append(f"Длина документа: {len(content)} символов")
        
        if result.issues:
            report.append("\n🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for issue in result.issues:
                report.append(f"  {issue}")
        
        if result.warnings:
            report.append("\n🟡 ПРЕДУПРЕЖДЕНИЯ:")
            for warning in result.warnings:
                report.append(f"  {warning}")
        
        if result.suggestions:
            report.append("\n💡 РЕКОМЕНДАЦИИ:")
            for suggestion in result.suggestions:
                report.append(f"  {suggestion}")
        
        if result.auto_fixes:
            report.append("\n🔧 АВТОМАТИЧЕСКИЕ ИСПРАВЛЕНИЯ:")
            for fix_type, fix_value in result.auto_fixes.items():
                report.append(f"  {fix_type}: {fix_value}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


def main():
    """Пример использования валидатора"""
    validator = DocumentQualityValidator()
    
    # Пример problematic документа
    test_content = """В: Как подключить принтер?
О: Подключите принтер к компьютеру через USB кабель. Установите драйверы с диска. Перезагрузите компьютер."""
    
    test_metadata = {}
    
    # Валидация
    print(validator.generate_validation_report(test_content, test_metadata))
    
    # Применение автоматических исправлений
    result = validator.validate_document(test_content, test_metadata)
    
    if result.auto_fixes:
        print("\nПрименение автоматических исправлений...")
        
        if 'keywords' in result.auto_fixes:
            test_metadata = validator.add_suggested_keywords(test_metadata, test_content)
            print(f"✅ Добавлены keywords: {test_metadata['keywords']}")
        
        if 'category' in result.auto_fixes:
            test_metadata = validator.add_suggested_category(test_metadata, test_content)
            print(f"✅ Добавлена категория: {test_metadata.get('category')}")
    
    # Предложение синонимов
    improved_content = validator.suggest_synonyms_addition(test_content)
    if improved_content != test_content:
        print(f"\n✅ Улучшенный текст с синонимами:\n{improved_content}")
    
    # Разбиение длинного чанка
    long_content = "A" * 1000  # Слишком длинный чанк
    chunks = validator.split_long_chunk(long_content)
    print(f"\n✅ Длинный чанк разбит на {len(chunks)} частей")


if __name__ == '__main__':
    main()
