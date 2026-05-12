#!/usr/bin/env python3
"""
API сервер для запуска RAG quality analytics
Запускается внутри контейнера max-bot-webhook
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import threading
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class AnalyticsAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler для запуска аналитики"""
    
    def log_message(self, format, *args):
        """Подавляем стандартные логи"""
        pass
    
    def do_GET(self):
        """GET /health - проверка здоровья сервиса"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'service': 'rag-analytics-api',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """POST /run-evaluation - запуск оценки"""
        if self.path == '/run-evaluation':
            # Получаем параметры из query string или body
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode('utf-8'))
            else:
                # Default parameters
                params = {
                    'sample_size': 50,
                    'top_k': '3,5,10'
                }
            
            sample_size = params.get('sample_size', 50)
            top_k = params.get('top_k', '3,5,10')
            
            # Запускаем оценку в background thread
            thread = threading.Thread(
                target=self.run_evaluation,
                args=(sample_size, top_k)
            )
            thread.daemon = True
            thread.start()
            
            self.send_response(202)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'started',
                'message': 'Evaluation started in background',
                'parameters': {
                    'sample_size': sample_size,
                    'top_k': top_k
                },
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def run_evaluation(self, sample_size, top_k):
        """Запускает скрипт оценки"""
        try:
            print(f"\n{'='*80}")
            print(f"ЗАПУСК ОЦЕНКИ КАЧЕСТВА RAG")
            print(f"Sample size: {sample_size}, Top-K: {top_k}")
            print(f"{'='*80}\n")
            
            cmd = [
                sys.executable,
                '/app/scripts/rag_quality_analytics.py',
                '--sample', str(sample_size),
                '--top-k', top_k
            ]
            
            result = subprocess.run(
                cmd,
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                print("✅ Оценка завершена успешно")
                print(result.stdout[-500:])  # Last 500 chars
            else:
                print(f"❌ Оценка завершилась с ошибкой: {result.returncode}")
                print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print("❌ Превышено время выполнения (10 минут)")
        except Exception as e:
            print(f"❌ Ошибка при запуске оценки: {e}")


def main():
    """Запуск API сервера"""
    port = int(os.getenv('ANALYTICS_API_PORT', 8766))
    
    server = HTTPServer(('0.0.0.0', port), AnalyticsAPIHandler)
    
    print(f"{'='*80}")
    print(f"RAG Analytics API Server запущен на порту {port}")
    print(f"Endpoints:")
    print(f"  GET  /health         - проверка здоровья")
    print(f"  POST /run-evaluation - запуск оценки")
    print(f"{'='*80}\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server.shutdown()


if __name__ == '__main__':
    main()
