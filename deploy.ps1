# Скрипт для сборки и запуска бота в Docker (Windows)

Write-Host "🐳 Сборка Docker образа..." -ForegroundColor Cyan
docker-compose build

Write-Host ""
Write-Host "🚀 Запуск контейнера..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "✅ Бот запущен!" -ForegroundColor Green
Write-Host ""
Write-Host "Полезные команды:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f     # Просмотр логов"
Write-Host "  docker-compose down        # Остановка бота"
Write-Host "  docker-compose restart     # Перезапуск бота"
Write-Host "  docker-compose ps          # Статус контейнера"
