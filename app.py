import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from config import Config
from database import init_db, test_db_connection
from views import register_blueprints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("BloodBankAPI")

def _mask_sensitive_data(data):
    """Recursively mask passwords and tokens in log dumps."""
    if not isinstance(data, dict):
        return data
    masked = {}
    for k, v in data.items():
        if any(secret in k.lower() for secret in ['password', 'token', 'secret', 'key']):
            masked[k] = '***REDACTED***'
        elif isinstance(v, dict):
            masked[k] = _mask_sensitive_data(v)
        else:
            masked[k] = v
    return masked

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for all routes (important for Flutter Web / Mobile)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Middleware: Log incoming API requests
    @app.before_request
    def log_request_start():
        g.start_time = time.time()
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        method = request.method
        path = request.path
        query = request.query_string.decode('utf-8')
        full_path = f"{path}?{query}" if query else path

        body_summary = ""
        if request.is_json and request.get_data():
            try:
                body_json = request.get_json(silent=True)
                if body_json:
                    body_summary = f" | Body: {json.dumps(_mask_sensitive_data(body_json))}"
            except Exception:
                pass

        logger.info(f"👉 [API REQ] {method} {full_path} | Client: {client_ip}{body_summary}")

    # Middleware: Log outgoing API responses
    @app.after_request
    def log_response_end(response):
        duration_ms = 0
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000

        status_code = response.status_code
        status_icon = "✅" if status_code < 400 else "⚠️" if status_code < 500 else "❌"
        
        logger.info(
            f"👈 [API RES] {status_icon} {request.method} {request.path} -> "
            f"[{status_code}] ({duration_ms:.1f}ms) | Content-Type: {response.content_type}"
        )
        return response

    # Register MVC view routes
    register_blueprints(app)

    @app.route('/')
    def root():
        return jsonify({
            'status': 'ONLINE',
            'service': 'Blood Bank Management System API',
            'version': '1.0.0',
            'architecture': 'MVC (Model-View-Controller)',
            'database': 'Neon PostgreSQL',
            'health': '/health'
        }), 200

    @app.route('/health')
    def health():
        db_ok, latency = test_db_connection()
        return jsonify({
            'status': 'OK' if db_ok else 'DEGRADED',
            'code': 200 if db_ok else 500,
            'database_connected': db_ok,
            'database_latency_ms': round(latency, 2),
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if db_ok else 500

    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"⚠️ [400 BAD REQUEST] {request.path}: {e}")
        return jsonify({'success': False, 'message': 'Invalid request parameters. Please verify your input.'}), 400

    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"🔍 [404 NOT FOUND] {request.path}")
        return jsonify({'success': False, 'message': 'The requested resource was not found.'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"❌ [500 INTERNAL SERVER ERROR] {request.path}:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'An unexpected server error occurred. Please try again later.'}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.error(f"🔥 [UNHANDLED EXCEPTION] {request.path}:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred. Please try again later.'}), 500

    return app

if __name__ == '__main__':
    print("\n" + "="*65)
    print("🩸 BLOOD BANK MANAGEMENT SYSTEM - BACKEND INITIALIZATION")
    print("="*65)
    init_db()
    app = create_app()
    port = Config.PORT
    print(f"🚀 API server running at: http://0.0.0.0:{port}")
    print(f"📋 Health check endpoint: http://localhost:{port}/health")
    print("="*65 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)

