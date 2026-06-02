# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Flask application entry point"""

import os
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity

# Load .env file if it exists (before config is loaded)
# This must happen before importing config to ensure env vars are available
try:
    from dotenv import load_dotenv
    # Load .env from project root directory
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)  # override=True to ensure .env values take precedence
        # Use print since logging is not configured yet
        print(f"✓ Loaded .env file from {env_path}")
        # Verify ENCRYPTION_KEY is loaded
        if os.getenv('ENCRYPTION_KEY'):
            print(f"✓ ENCRYPTION_KEY is set (length: {len(os.getenv('ENCRYPTION_KEY'))})")
        else:
            print("⚠ ENCRYPTION_KEY not found in .env file")
    else:
        print(f"⚠ .env file not found at {env_path}")
except ImportError:
    # python-dotenv not installed, skip .env loading
    print("⚠ python-dotenv not installed, skipping .env file loading")
    print("  Install it with: pip install python-dotenv")

from config import config
from db import init_db, db
from utils.encryption import init_encryption
from celery_app import make_celery

# Initialize extensions
jwt = JWTManager()

def limiter_key_func():
    """Custom key function for rate limiting: use user ID if authenticated, otherwise IP"""
    try:
        identity = get_jwt_identity()
        if identity:
            return f"user:{identity}"
    except:
        pass
    return get_remote_address()

limiter = Limiter(
    key_func=limiter_key_func,
    default_limits=["5000 per day", "1000 per hour"]
)


def create_app(config_name=None):
    """Create and configure Flask application"""
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize extensions
    init_db(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Initialize encryption
    init_encryption(app)
    
    # Initialize Celery with app context
    make_celery(app)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(app.config['LOG_FILE']),
            logging.StreamHandler()
        ]
    )
    
    # Register blueprints
    from api import auth, scanner, hosts, virtualization, tags, applications
    from api import config as config_bp
    from api import import_api, collections
    app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
    app.register_blueprint(scanner.bp, url_prefix='/api/v1/scans')
    app.register_blueprint(hosts.bp, url_prefix='/api/v1/hosts')
    app.register_blueprint(virtualization.bp, url_prefix='/api/v1/platforms')
    app.register_blueprint(tags.bp, url_prefix='/api/v1/tags')
    app.register_blueprint(applications.bp, url_prefix='/api/v1/applications')
    app.register_blueprint(config_bp.bp, url_prefix='/api/v1/config')
    app.register_blueprint(import_api.bp, url_prefix='/api/v1/import')
    app.register_blueprint(collections.bp, url_prefix='/api/v1/collections')
    
    # Health check endpoint
    @app.route('/api/v1/health')
    def health():
        """Health check endpoint"""
        try:
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    @app.errorhandler(404)
    def not_found(error):
        return {'code': 404, 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'code': 500, 'message': 'Internal server error'}, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)