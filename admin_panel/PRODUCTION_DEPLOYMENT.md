# Руководство по Production Deployment - Admin Panel

**Версия:** 1.0  
**Последнее обновление:** 27 апреля 2026

---

## 🎯 Обзор

Это руководство охватывает безопасное production развертывание Admin Panel с:
- HTTPS шифрованием (SSL/TLS)
- Reverse proxy (Nginx)
- Базовой аутентификацией (Basic Auth)
- Whitelist IP (опционально)
- Docker конфигурацией

---

## 📋 Требования

1. **Доменное имя**, указывающее на ваш сервер (например, `admin.yourdomain.com`)
2. **Root доступ** к серверу
3. **Docker и Docker Compose** установлены
4. **Nginx** установлен (`sudo apt install nginx`)
5. **Фаервол** настроен (рекомендуется UFW)

---

## 🚀 Пошаговое развертывание

### Шаг 1: Подготовка переменных окружения

```bash
# Перейдите в директорию admin_panel
cd /path/to/service-desk-assistant/admin_panel

# Скопируйте пример env файла
cp .env.example .env

# Отредактируйте с вашими значениями
nano .env
```

**Содержимое .env:**
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Admin Credentials (USE STRONG PASSWORDS!)
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=SuperSecureP@ssw0rd!2024

# Optional: JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
```

⚠️ **ВАЖНО:** Никогда не коммитьте файл `.env` в Git!

---

### Шаг 2: Настройка фаервола (UFW)

```bash
# Включите UFW если еще не включен
sudo ufw enable

# Разрешите SSH
sudo ufw allow 22/tcp

# Разрешите HTTP и HTTPS (для Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Заблокируйте прямой доступ к порту Streamlit (доступ только через Nginx)
sudo ufw deny 8501/tcp

# Проверьте статус
sudo ufw status verbose
```

---

### Шаг 3: Настройка SSL сертификата (Let's Encrypt)

```bash
# Сделайте скрипт исполняемым
chmod +x admin_panel/setup_ssl.sh

# Запустите настройку SSL (замените на ваш домен)
sudo ./admin_panel/setup_ssl.sh admin.yourdomain.com
```

**Альтернативный ручной метод:**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d admin.yourdomain.com

**Сертификаты будут расположены:**
# /etc/letsencrypt/live/admin.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/admin.yourdomain.com/privkey.pem
```

---

### Шаг 4: Конфигурация Nginx

```bash
# Скопируйте конфиг nginx
sudo cp admin_panel/nginx.conf /etc/nginx/sites-available/admin-panel.conf

# Отредактируйте с вашим доменом
sudo nano /etc/nginx/sites-available/admin-panel.conf
```

**Обновите эти строки в nginx.conf:**
```nginx
server_name admin.yourdomain.com;  # Your actual domain

ssl_certificate /etc/letsencrypt/live/admin.yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/admin.yourdomain.com/privkey.pem;
```

**Включите сайт:**
```bash
# Создайте символическую ссылку
sudo ln -s /etc/nginx/sites-available/admin-panel.conf /etc/nginx/sites-enabled/

# Удалите сайт по умолчанию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Протестируйте конфигурацию
sudo nginx -t

# Перезагрузите Nginx
sudo systemctl reload nginx
```

---

### Шаг 5: Настройка базовой аутентификации

```bash
# Сделайте скрипт исполняемым
chmod +x admin_panel/setup_basic_auth.sh

# Запустите настройку
sudo ./admin_panel/setup_basic_auth.sh
```

**Следуйте подсказкам:**
```
Enter admin username [admin]: myadmin
Enter admin password: ********
```

Это создает файл `/etc/nginx/.htpasswd` с зашифрованными учетными данными.

---

### Шаг 6: Сборка и запуск Docker контейнеров

```bash
# Перейдите в корень проекта
cd /path/to/service-desk-assistant

# Пересоберите образ admin panel (для включения последних изменений)
docker compose build admin-panel

# Запустите все сервисы
docker compose up -d

# Проверьте статус
docker compose ps

# Просмотрите логи
docker logs -f admin-panel
```

---

### Шаг 7: Проверка развертывания

**Протестируйте HTTPS доступ:**
```bash
curl -I https://admin.yourdomain.com
```

**Ожидаемый ответ:**
```
HTTP/2 401
www-authenticate: Basic realm="Admin Panel - Restricted Access"
```

**Протестируйте в браузере:**
1. Откройте `https://admin.yourdomain.com`
2. Введите учетные данные Basic Auth (из Шага 5)
3. Введите учетные данные для входа в Streamlit (из .env)
4. Вы должны увидеть dashboard Admin Panel

---

## 🔒 Контрольный список безопасности

- ✅ HTTPS включен с валидным SSL сертификатом
- ✅ HTTP перенаправляется на HTTPS
- ✅ Базовая аутентификация настроена
- ✅ Учетные данные Streamlit изменены с значений по умолчанию
- ✅ Порт 8501 заблокирован от внешнего доступа (фаервол)
- ✅ Файл .env не закоммичен в Git
- ✅ Service role key хранится в секрете
- ✅ Регулярные обновления безопасности запланированы

---

## 🛠️ Обслуживание

### Продление SSL сертификата

Сертификаты Let's Encrypt истекают каждые 90 дней. Автопродление обычно настроено, но проверьте:

```bash
# Протестируйте автопродление
sudo certbot renew --dry-run

# Ручное продление если необходимо
sudo certbot renew

# Перезагрузите Nginx после продления
sudo systemctl reload nginx
```

### Обновление Admin Panel

```bash
# Получите последний код
git pull origin main

# Пересоберите и перезапустите
docker compose down admin-panel
docker compose build admin-panel
docker compose up -d admin-panel
```

### Резервное копирование конфигурации

```bash
# Резервное копирование важных файлов
sudo tar czf admin-panel-backup-$(date +%Y%m%d).tar.gz \
  /etc/nginx/sites-available/admin-panel.conf \
  /etc/nginx/.htpasswd \
  /etc/letsencrypt/live/admin.yourdomain.com/ \
  /path/to/service-desk-assistant/.env
```

### Мониторинг

```bash
# Проверьте здоровье контейнера
docker compose ps

# Просмотрите логи
docker logs --tail 100 admin-panel

# Логи в реальном времени
docker logs -f admin-panel

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/admin-panel-access.log
sudo tail -f /var/log/nginx/admin-panel-error.log
```

---

## 🐛 Устранение неполадок

### Проблема: "502 Bad Gateway"

**Решение:**
```bash
# Проверьте работает ли контейнер admin-panel
docker ps | grep admin-panel

# Проверьте логи контейнера
docker logs admin-panel

# Перезапустите контейнер
docker compose restart admin-panel

# Проверьте логи ошибок Nginx
sudo tail -50 /var/log/nginx/admin-panel-error.log
```

### Проблема: "Ошибка SSL сертификата"

**Решение:**
```bash
# Проверьте существует ли сертификат
ls -la /etc/letsencrypt/live/admin.yourdomain.com/

# Обновите сертификат
sudo certbot renew --force-renewal

# Проверьте конфиг Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### Проблема: "Базовая аутентификация не работает"

**Решение:**
```bash
# Проверьте существует ли файл .htpasswd
ls -la /etc/nginx/.htpasswd

# Проверьте права доступа к файлу
sudo chmod 640 /etc/nginx/.htpasswd
sudo chown root:www-data /etc/nginx/.htpasswd

# Протестируйте аутентификацию
curl -u username:password https://admin.yourdomain.com

# Перегенерируйте если необходимо
sudo htpasswd -c /etc/nginx/.htpasswd newusername
```

### Проблема: "Соединение отклонено"

**Решение:**
```bash
# Проверьте фаервол
sudo ufw status

# Убедитесь что порты открыты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверьте работает ли Nginx
sudo systemctl status nginx

# Перезапустите Nginx
sudo systemctl restart nginx
```

---

## 📊 Оптимизация производительности

### Тюнинг Nginx

Отредактируйте `/etc/nginx/nginx.conf`:

```nginx
http {
    # Worker connections
    worker_connections 1024;
    
    # Gzip сжатие
    gzip on;
    gzip_types text/plain application/json text/css application/javascript;
    
    # Кэширование статических ресурсов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Ограничения ресурсов Docker

Добавьте в `docker-compose.yml`:

```yaml
services:
  admin-panel:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

---

## 🔐 Расширенная безопасность (Опционально)

### Whitelist IP

Добавьте в `nginx.conf`:

```nginx
server {
    # ... существующий конфиг ...
    
    # Разрешить только определенные IP
    allow 192.168.1.100;   # IP вашего офиса
    allow 10.0.0.0/8;      # Внутренняя сеть
    deny all;              # Блокировать всех остальных
}
```

### Интеграция Fail2Ban

Установите и настройте Fail2Ban для блокировки попыток brute force:

```bash
sudo apt install fail2ban

# Создайте jail для Nginx
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/*error*.log
maxretry = 5
bantime = 3600
```

```bash
sudo systemctl restart fail2ban
```

### Двухфакторная аутентификация (Будущее улучшение)

Для повышенной безопасности рассмотрите внедрение:
- OAuth2 с Google/GitHub
- TOTP (Time-based One-Time Password)
- LDAP/Active Directory интеграция

---

## 📝 Быстрая справка по командам

```bash
# Запуск сервисов
docker compose up -d

# Остановка сервисов
docker compose down

# Просмотр логов
docker logs -f admin-panel

# Перезапуск admin panel
docker compose restart admin-panel

# Пересборка после изменений кода
docker compose build admin-panel && docker compose up -d admin-panel

# Проверка срока действия SSL
sudo certbot certificates

# Обновление SSL
sudo certbot renew

# Тест конфига Nginx
sudo nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx

# Проверка фаервола
sudo ufw status
```

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker logs admin-panel`
2. Проверьте Nginx: `sudo tail -f /var/log/nginx/admin-panel-error.log`
3. Проверьте SSL: `sudo certbot certificates`
4. Протестируйте подключение: `curl -I https://admin.yourdomain.com`

---

## ✅ Контрольный список проверки развертывания

После развертывания проверьте:

- [ ] HTTPS работает: `https://admin.yourdomain.com`
- [ ] HTTP перенаправляется на HTTPS
- [ ] Появляется запрос Basic Auth
- [ ] Вход в Streamlit работает
- [ ] Можно просматривать документы
- [ ] Можно добавлять/редактировать/удалять документы
- [ ] Валидация качества работает
- [ ] Страница аналитики загружается
- [ ] Нет ошибок в логах
- [ ] SSL сертификат валиден
- [ ] Фаервол блокирует порт 8501
- [ ] Автопродление настроено

---

**Поздравляем! Ваш Admin Panel теперь безопасно развернут в production! 🎉**
