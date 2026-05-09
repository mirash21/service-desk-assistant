# Admin Panel - Service Desk Assistant

Веб-интерфейс для управления ботом технической поддержки.

## 🚀 Быстрый старт

### Локальный запуск (для разработки)

```bash
# 1. Установите зависимости
pip install -r admin_panel/requirements.txt

# 2. Запустите Streamlit
streamlit run admin_panel/app.py --server.port=8501

# 3. Откройте браузер
http://localhost:8501
```

⚠️ **Важно:** Перед первым запуском необходимо настроить credentials (см. раздел "Конфигурация").

### Docker запуск

```bash
# Build и запуск
docker compose up -d admin-panel

# Проверка логов
docker logs -f admin-panel

# Доступ
http://localhost:8501
```

## 📋 Возможности

### ✅ Реализовано (Phase 1 - MVP)

- 🔐 Аутентификация администратора
- 📚 Просмотр всех документов с пагинацией
- 🔍 Фильтрация по категории и поиск
- ➕ Добавление новых Q&A пар
- ✏️ Редактирование существующих документов
- 🗑️ Удаление документов с подтверждением
- ✅ Real-time валидация качества
- 🔧 Автоматические исправления (keywords, category, synonyms)
- 📊 Базовая аналитика и метрики
- ❓ Просмотр unanswered questions
- 📥 Экспорт данных

### 🎯 Planned (Phase 2-4)

- 📈 Advanced analytics dashboard с графиками
- ⚙️ Настройки системы (поиск, LLM параметры)
- 📦 Batch operations (import/export CSV)
- 🔒 JWT authentication
- 📝 Activity logging
- 🧪 Unit tests

## 🏗️ Архитектура

```
admin_panel/
├── app.py                      # Главное приложение
├── pages/                      # Страницы
│   ├── 0_🔐_Login.py          # Вход
│   ├── 1_📚_Documents.py      # Управление документами
│   └── 2_📊_Analytics.py      # Аналитика
├── components/                 # UI компоненты
│   ├── document_table.py       # Таблица документов
│   ├── document_editor.py      # Формы добавления/редактирования
│   └── quality_indicator.py    # Индикатор качества
├── api/                        # API layer
│   └── rag_api.py              # CRUD операции
├── utils/                      # Утилиты
├── requirements.txt            # Зависимости
└── Dockerfile                  # Docker конфигурация
```

## 🔧 Конфигурация

### Environment Variables

Создайте `.env` файл в корне проекта:

```bash
cp admin_panel/.env.example .env
nano .env
```

Заполните необходимые переменные:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Admin Credentials (ОБЯЗАТЕЛЬНО измените!)
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password_here
```

⚠️ **Важно:** Без настроенных `ADMIN_USERNAME` и `ADMIN_PASSWORD` вход в систему будет невозможен!

### Изменение пароля

Отредактируйте `.env` файл:

```bash
nano .env
```

Измените значения:
```env
ADMIN_USERNAME=new_username
ADMIN_PASSWORD=new_secure_password
```

Перезапустите контейнер:
```bash
docker compose restart admin-panel
```

## 📖 Использование

### Добавление документа

1. Перейдите на страницу **Documents**
2. Выберите вкладку **Add New Document**
3. Заполните:
   - Category (выберите из списка)
   - Question (вопрос пользователя)
   - Answer (ответ с решением)
4. Нажмите **Preview Validation** для проверки качества
5. Нажмите **Save Document**

**Auto-fix автоматически:**
- ✅ Добавит keywords на основе контента
- ✅ Определит категорию если не указана
- ✅ Предложит синонимы для常见ных терминов

### Редактирование документа

1. Найдите документ в списке
2. Нажмите **✏️ Edit**
3. Внесите изменения
4. Нажмите **Update**

### Удаление документа

1. Найдите документ в списке
2. Нажмите **🗑️ Delete**
3. Подтвердите удаление

### Фильтрация и поиск

Используйте sidebar для фильтрации:
- **Category**: фильтр по категории
- **Search**: поиск по содержимому

## 🎨 Скриншоты

### Login Page
![Login](screenshots/login.png)

### Documents List
![Documents](screenshots/documents.png)

### Add Document with Validation
![Add Document](screenshots/add_document.png)

### Analytics Dashboard
![Analytics](screenshots/analytics.png)

## 🧪 Testing

### Manual Testing Checklist

- [ ] Login с правильными credentials
- [ ] Login с неправильными credentials (должен отказать)
- [ ] Просмотр списка документов
- [ ] Фильтрация по категории
- [ ] Поиск документов
- [ ] Добавление нового документа
- [ ] Валидация перед сохранением
- [ ] Редактирование документа
- [ ] Удаление документа с подтверждением
- [ ] Пагинация работает корректно
- [ ] Logout функциональность

## 🐛 Troubleshooting

### Проблема: "Module not found"

**Решение:**
```bash
# Убедитесь что dependencies установлены
pip install -r admin_panel/requirements.txt

# Или пересоберите Docker image
docker compose build admin-panel
```

### Проблема: "Cannot connect to Supabase"

**Решение:**
```bash
# Проверьте environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Или проверьте .env файл
cat .env
```

### Проблема: "Port 8501 already in use"

**Решение:**
```bash
# Измените порт в docker-compose.yml
ports:
  - "8502:8501"  # Используйте другой host port

# Или остановите другой процесс
lsof -i :8501
kill <PID>
```

## 📊 Monitoring

### Просмотр логов

```bash
# Docker logs
docker logs -f admin-panel

# Streamlit logs (local)
# Logs отображаются в терминале где запущен streamlit
```

### Health Check

Admin panel доступен по адресу:
```
http://localhost:8501/healthz
```

## 🔒 Security

### Best Practices

1. **Измените default password** перед production deployment
2. **Используйте HTTPS** в production
3. **Не коммитьте .env файлы** в git
4. **Регулярно обновляйте** dependencies

### Production Deployment

```yaml
# docker-compose.prod.yml
services:
  admin-panel:
    environment:
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
    networks:
      - internal_network  # Не expose напрямую
```

## 🤝 Contributing

### Development Workflow

1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit PR

### Code Style

- Follow PEP 8 для Python
- Use type hints
- Add docstrings to functions
- Write meaningful commit messages

## 📝 License

MIT License

## 📞 Support

Если возникли вопросы:

1. Проверьте этот README
2. Посмотрите логи: `docker logs admin-panel`
3. Создайте issue в GitHub repository

---

**Version:** 1.0.0  
**Last Updated:** April 27, 2026
