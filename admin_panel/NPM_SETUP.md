# Настройка Nginx Proxy Manager для Admin Panel

**Домен:** `admin-bot.vaib-cod.ru`  
**Целевой сервис:** Admin Panel (Streamlit)  
**Порт:** 8501  
**Дата:** 27 апреля 2026

---

## 📋 Предварительные требования

1. ✅ Admin Panel запущен в Docker контейнере
2. ✅ Контейнер подключен к сети `npm_network`
3. ✅ Домен `admin-bot.vaib-cod.ru` настроен в DNS (A-запись на IP сервера)
4. ✅ Nginx Proxy Manager доступен (обычно порт 81)

---

## 🚀 Пошаговая настройка

### Шаг 1: Проверка DNS записи

Убедитесь, что домен указывает на ваш сервер:

```bash
# Проверьте A-запись
nslookup admin-bot.vaib-cod.ru

# Или используйте dig
dig admin-bot.vaib-cod.ru
```

**Ожидаемый результат:**
```
Name:   admin-bot.vaib-cod.ru
Address: <IP вашего сервера>
```

Если запись отсутствует, добавьте A-запись в панели управления reg.ru:
- **Тип:** A
- **Имя/Поддомен:** admin-bot
- **Значение/IP:** `<IP вашего сервера>`
- **TTL:** 600 (или автоматически)

---

### Шаг 2: Доступ к Nginx Proxy Manager

Откройте браузер и перейдите к NPM:

```
http://<IP сервера>:81
или
https://npm.yourdomain.com (если настроено)
```

**Login credentials** (изменились при первой настройке):
- Email: ваш email
- Password: ваш пароль

---

### Шаг 3: Создание Proxy Host

1. **Перейдите во вкладку "Hosts" → "Proxy Hosts"**

2. **Нажмите кнопку "Add Proxy Host"** (в правом верхнем углу)

3. **Заполните форму:**

#### Tab: Details

**Domain Names:**
```
admin-bot.vaib-cod.ru
```

**Scheme:**
```
http
```

**Forward Hostname / IP:**
```
admin-panel
```
⚠️ **ВАЖНО:** Используйте имя контейнера, НЕ IP адрес!

**Forward Port:**
```
8501
```

#### Tab: SSL

**SSL Certificate:**
```
Request a new SSL certificate
```

✅ **Force SSL** - Включите (обязательно!)

✅ **HTTP/2 Support** - Включите (рекомендуется)

**Email Address for Let's Encrypt:**
```
ваш-email@example.com
```

#### Tab: Advanced (опционально)

Добавьте custom nginx configuration для WebSocket support (требуется для Streamlit):

```nginx
location /stream {
    proxy_pass http://admin-panel:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_buffering off;
    proxy_cache off;
}

location /_stcore/stream {
    proxy_pass http://admin-panel:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_buffering off;
    proxy_cache off;
}
```

4. **Нажмите "Save"**

---

### Шаг 4: Проверка SSL сертификата

NPM автоматически запросит SSL сертификат от Let's Encrypt.

**Проверьте статус:**
1. Вернитесь к списку Proxy Hosts
2. Найдите `admin-bot.vaib-cod.ru`
3. Статус SSL должен быть **"Valid"** (зеленый)

**Если возникли ошибки:**
- Проверьте что DNS запись активна
- Убедитесь что порт 80 открыт (для challenge)
- Проверьте логи NPM

---

### Шаг 5: Тестирование доступа

Откройте браузер и перейдите:

```
https://admin-bot.vaib-cod.ru
```

**Ожидаемое поведение:**
1. Запрос Basic Authentication (если настроен в Nginx config)
2. Страница входа Streamlit
3. После входа - dashboard Admin Panel

---

## 🔧 Troubleshooting

### Проблема 1: "502 Bad Gateway"

**Причины:**
- Контейнер admin-panel не запущен
- Неправильное имя хоста в NPM
- Контейнер не в той сети

**Решение:**
```bash
# Проверьте что контейнер запущен
docker ps | grep admin-panel

# Проверьте сети контейнера
docker inspect admin-panel | grep Networks

# Убедитесь что контейнер в npm_network
docker network connect npm_network admin-panel

# Перезапустите контейнер
docker compose restart admin-panel
```

---

### Проблема 2: "SSL Certificate Error"

**Причины:**
- DNS запись не активна
- Порт 80 заблокирован фаерволом
- Let's Encrypt rate limit

**Решение:**
```bash
# Проверьте DNS
nslookup admin-bot.vaib-cod.ru

# Откройте порт 80 временно
sudo ufw allow 80/tcp

# Проверьте логи NPM
docker logs nginx-proxy-manager

# Принудительно обновите сертификат в NPM UI
```

---

### Проблема 3: "WebSocket connection failed"

Streamlit использует WebSocket для real-time обновлений.

**Решение:**
Добавьте в Advanced config NPM:

```nginx
location / {
    proxy_pass http://admin-panel:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_buffering off;
    proxy_cache off;
}
```

Или используйте готовый Advanced config из Шага 3.

---

### Проблема 4: Медленная загрузка / Таймауты

**Решение:**
Увеличьте таймауты в Advanced config:

```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

---

## 🔒 Дополнительная безопасность

### Опция 1: Basic Auth через NPM

В Nginx Proxy Manager можно добавить Basic Authentication:

1. В Proxy Host settings перейдите на вкладку **"Access List"**
2. Создайте новый Access List
3. Добавьте username/password
4. Привяжите к Proxy Host

### Опция 2: IP Whitelist

Ограничьте доступ по IP в Advanced config:

```nginx
allow 192.168.1.100;  # Ваш IP
allow 10.0.0.0/8;     # Внутренняя сеть
deny all;
```

### Опция 3: Rate Limiting

Защита от brute force:

```nginx
limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=10r/m;

location / {
    limit_req zone=admin_limit burst=5 nodelay;
    proxy_pass http://admin-panel:8501;
    ...
}
```

---

## 📊 Мониторинг

### Проверка логов NPM

```bash
# Логи Nginx Proxy Manager
docker logs nginx-proxy-manager

# Логи в реальном времени
docker logs -f nginx-proxy-manager

# Только ошибки
docker logs nginx-proxy-manager 2>&1 | grep error
```

### Проверка логов Admin Panel

```bash
docker logs admin-panel
docker logs -f admin-panel
```

### Проверка SSL статуса

```bash
# Проверьте сертификат
curl -I https://admin-bot.vaib-cod.ru

# Детальная информация
openssl s_client -connect admin-bot.vaib-cod.ru:443 -servername admin-bot.vaib-cod.ru
```

---

## 🔄 Обновление конфигурации

Если нужно изменить настройки:

1. **Через NPM UI:**
   - Откройте Proxy Host
   - Внесите изменения
   - Нажмите Save
   - NPM автоматически перезагрузит конфиг

2. **Через Docker:**
   ```bash
   # Перезапуск NPM
   docker restart nginx-proxy-manager
   
   # Перезапуск Admin Panel
   docker compose restart admin-panel
   ```

---

## ✅ Контрольный список

После настройки проверьте:

- [ ] DNS запись `admin-bot.vaib-cod.ru` активна
- [ ] Контейнер `admin-panel` запущен
- [ ] Контейнер в сети `npm_network`
- [ ] Proxy Host создан в NPM
- [ ] Forward Hostname: `admin-panel`
- [ ] Forward Port: `8501`
- [ ] SSL сертификат получен (статус Valid)
- [ ] Force SSL включен
- [ ] HTTPS работает: `https://admin-bot.vaib-cod.ru`
- [ ] HTTP перенаправляется на HTTPS
- [ ] Streamlit login page загружается
- [ ] Можно войти в систему
- [ ] Все функции работают
- [ ] Нет ошибок в логах

---

## 📝 Quick Commands

```bash
# Проверить статус контейнера
docker ps | grep admin-panel

# Проверить сети
docker network ls | grep npm

# Подключить контейнер к сети (если нужно)
docker network connect npm_network admin-panel

# Перезапустить Admin Panel
docker compose restart admin-panel

# Перезапустить NPM
docker restart nginx-proxy-manager

# Проверить DNS
nslookup admin-bot.vaib-cod.ru

# Протестировать HTTPS
curl -I https://admin-bot.vaib-cod.ru

# Просмотреть логи NPM
docker logs nginx-proxy-manager --tail 50

# Просмотреть логи Admin Panel
docker logs admin-panel --tail 50
```

---

## 🎯 Итоговая архитектура

```
Internet
    │
    ▼
┌──────────────────┐
│  DNS (reg.ru)    │  admin-bot.vaib-cod.ru → IP сервера
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Firewall (UFW)  │  Разрешает 80, 443
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Nginx Proxy     │  SSL termination, routing
│  Manager         │  admin-bot.vaib-cod.ru → admin-panel:8501
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Docker Network  │  npm_network
│  (npm_network)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Admin Panel     │  Streamlit на порту 8501
│  Container       │  Внутри Docker
└──────────────────┘
```

---

## 💡 Tips & Best Practices

1. **Всегда используйте hostname контейнера**, а не IP адрес
2. **Включайте Force SSL** для всех production сервисов
3. **Настраивайте автообновление** SSL сертификатов
4. **Мониторьте логи** регулярно
5. **Делайте backup** конфигурации NPM
6. **Тестируйте после изменений** в браузере incognito mode

---

**Готово! Admin Panel теперь доступен по адресу: https://admin-bot.vaib-cod.ru** 🎉
