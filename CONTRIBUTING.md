# Contributing to Service Desk Assistant

Спасибо за интерес к проекту! 🎉 Ваш вклад помогает сделать Service Desk Assistant лучше.

## 📋 Содержание

- [Code of Conduct](#code-of-conduct)
- [Как внести вклад](#как-внести-вклад)
- [Стандарты кода](#стандарты-кода)
- [Процесс Pull Request](#процесс-pull-request)
- [Сообщение об ошибках](#сообщение-об-ошибках)
- [Запрос новых функций](#запрос-новых-функций)

## Code of Conduct

Этот проект и все участники придерживаются [Code of Conduct](CODE_OF_CONDUCT.md). Участвуя, вы соглашаетесь соблюдать его.

## Как внести вклад

### 1. Fork репозитория

Нажмите кнопку "Fork" в правом верхнем углу страницы GitHub.

### 2. Клонируйте ваш fork

```bash
git clone https://github.com/your-username/service-desk-assistant.git
cd service-desk-assistant
```

### 3. Создайте ветку

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/your-bug-fix
```

**Именование веток:**
- `feature/` - для новых функций
- `fix/` - для исправления ошибок
- `docs/` - для документации
- `refactor/` - для рефакторинга кода

### 4. Внесите изменения

Следуйте стандартам кода (см. ниже).

### 5. Протестируйте изменения

```bash
# Проверка системы
python check_system.py

# Локальное тестирование
python main.py
```

### 6. Зафиксируйте изменения

```bash
git add .
git commit -m "feat: add new feature description"
```

**Формат коммитов:**
- `feat:` - новая функция
- `fix:` - исправление ошибки
- `docs:` - изменения в документации
- `style:` - форматирование кода
- `refactor:` - рефакторинг
- `test:` - добавление тестов
- `chore:` - обновление зависимостей

### 7. Отправьте в ваш fork

```bash
git push origin feature/your-feature-name
```

### 8. Создайте Pull Request

Перейдите на страницу вашего fork на GitHub и нажмите "Compare & pull request".

## Стандарты кода

### Python Style Guide

Мы следуем [PEP 8](https://peps.python.org/pep-0008/):

```python
# ✅ Правильно
def process_message(message: str) -> dict:
    """Обработка входящего сообщения.
    
    Args:
        message: Текст сообщения
        
    Returns:
        Словарь с результатом обработки
    """
    result = {"status": "ok"}
    return result

# ❌ Неправильно
def ProcessMessage(message):
    result={"status":"ok"}
    return result
```

### Требования к коду

1. **Type Hints** - используйте аннотации типов
2. **Docstrings** - документируйте все функции и классы
3. **Logging** - используйте логгер вместо print()
4. **Error Handling** - обрабатывайте исключения корректно
5. **DRY Principle** - не повторяйте код

### Пример документирования

```python
class MessageHandler:
    """Обработчик сообщений от MAX Messenger.
    
    Attributes:
        yandex: Сервис Yandex AI Studio
        rag_manager: Менеджер RAG системы
    """
    
    async def handle_text(self, text: str) -> str:
        """Обработка текстового сообщения.
        
        Args:
            text: Текст сообщения от пользователя
            
        Returns:
            Ответ бота
            
        Raises:
            ValueError: Если текст пустой
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Логика обработки
        return response
```

## Процесс Pull Request

### Checklist перед отправкой PR

- [ ] Код следует стандартам проекта
- [ ] Добавлены необходимые тесты
- [ ] Все тесты проходят успешно
- [ ] Документация обновлена
- [ ] Изменения протестированы локально
- [ ] Commit messages следуют конвенции

### Review процесс

1. Maintainer проверит ваш код
2. Могут быть запрошены изменения
3. После одобрения PR будет merged

**Время ответа:** Обычно в течение 2-3 дней

## Сообщение об ошибках

### Шаблон Issue для багов

```markdown
**Описание ошибки**
Четкое описание проблемы.

**Шаги воспроизведения**
1. Шаг 1
2. Шаг 2
3. ...

**Ожидаемое поведение**
Что должно было произойти.

**Скриншоты**
Если применимо.

**Окружение:**
- OS: [e.g. Windows 11, Ubuntu 22.04]
- Python: [e.g. 3.12]
- Версия бота: [e.g. 1.0.0]

**Дополнительная информация**
Любые другие детали.
```

## Запрос новых функций

### Шаблон Issue для фич

```markdown
**Описание функции**
Подробное описание предлагаемой функции.

**Мотивация**
Почему эта функция важна? Какую проблему решает?

**Пример использования**
```python
# Пример кода или сценарий использования
```

**Альтернативы**
Рассмотренные альтернативные решения.

**Дополнительная информация**
Любые другие детали.
```

## Разработка

### Настройка окружения разработчика

```bash
# 1. Fork и клонирование
git clone https://github.com/your-username/service-desk-assistant.git

# 2. Установка зависимостей
pip install -r requirements.txt
pip install pytest pytest-cov  # для тестирования

# 3. Pre-commit hooks (опционально)
pip install pre-commit
pre-commit install
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=.

# Конкретный тест
pytest tests/test_handler.py
```

### Линтеры

```bash
# Проверка стиля
flake8 .

# Проверка типов
mypy .

# Форматирование
black .
isort .
```

## Ресурсы

- [Документация проекта](README.md)
- [Инструкция по деплою](DEPLOY.md)
- [Python PEP 8](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Вопросы?

Не стесняйтесь создавать Issue с тегом `question` или связываться с maintainer'ами.

---

Спасибо за ваш вклад! 🚀
