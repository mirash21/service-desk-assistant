# Быстрая настройка Admin Panel в Nginx Proxy Manager

## 🎯 Параметры для NPM

**Proxy Host Configuration:**

| Параметр | Значение |
|----------|----------|
| **Domain Names** | `admin-bot.vaib-cod.ru` |
| **Scheme** | `http` |
| **Forward Hostname** | `admin-panel` |
| **Forward Port** | `8501` |
| **SSL Certificate** | Request new SSL certificate |
| **Force SSL** | ✅ Включить |
| **HTTP/2 Support** | ✅ Включить |
| **Email** | ваш-email@example.com |

---

## 📝 Advanced Config (WebSocket support)

Добавьте в вкладку **Advanced**:

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

---

## ✅ Проверка

После сохранения в NPM:

```bash
# Протестируйте доступ
curl -I https://admin-bot.vaib-cod.ru

# Ожидаемый ответ: HTTP/2 200 или 301
```

Откройте в браузере: **https://admin-bot.vaib-cod.ru**

---

## 🔧 Если не работает

```bash
# 1. Проверьте что контейнер запущен
docker ps | grep admin-panel

# 2. Проверьте сеть
docker inspect admin-panel | grep npm_network

# 3. Перезапустите контейнер
docker compose restart admin-panel

# 4. Проверьте логи NPM
docker logs nginx-proxy-manager --tail 50
```

---

**Готово!** 🚀
