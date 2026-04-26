#!/bin/bash
# Скрипт для сборки и запуска бота в Docker

set -e

echo "🐳 Сборка Docker образа..."
docker-compose build

echo ""
echo "🚀 Запуск контейнера..."
docker-compose up -d

echo ""
echo "✅ Бот запущен!"
echo ""
echo "Полезные команды:"
echo "  docker-compose logs -f     # Просмотр логов"
echo "  docker-compose down        # Остановка бота"
echo "  docker-compose restart     # Перезапуск бота"
echo "  docker-compose ps          # Статус контейнера"
