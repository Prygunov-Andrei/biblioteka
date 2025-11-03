#!/bin/bash
# Запуск всего проекта

cd /Users/andrei_prygunov/Dev/biblioteka

echo "🛑 Останавливаем процессы..."
pkill -9 -f "python.*manage.py"
pkill -9 -f "node.*react-scripts"
sleep 2

echo "🗑  Очищаем кэш..."
find . -name "*.pyc" -delete 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "🚀 Запускаем Backend..."
cd backend
python3 manage.py runserver 0.0.0.0:8000 > /tmp/backend.log 2>&1 &
cd ..
sleep 3

echo "🚀 Запускаем Frontend..."
cd frontend
npm start > /tmp/frontend.log 2>&1 &
sleep 5

echo ""
echo "✅ Приложение запущено!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo ""
echo "Логи:"
echo "  Backend:  tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"

