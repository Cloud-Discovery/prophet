# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Celery application configuration"""

from celery import Celery
from config import config
import os

config_name = os.environ.get('FLASK_ENV', 'default')
celery_config = config[config_name]

# Store Flask app reference for use in tasks
_flask_app = None

def make_celery(app=None):
    """Create and configure Celery application"""
    global _flask_app
    
    celery = Celery(
        'prophet',
        broker=celery_config.CELERY_BROKER_URL,
        backend=celery_config.CELERY_RESULT_BACKEND,
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour
        task_soft_time_limit=3300,  # 55 minutes
    )
    
    if app:
        # Store app reference
        _flask_app = app
        
        # Update configuration with Flask app config, but exclude CELERY_* keys
        # (new Celery versions don't support CELERY_ prefix)
        app_config = {k: v for k, v in app.config.items() if not k.startswith('CELERY_')}
        celery.conf.update(app_config)
        
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context"""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    else:
        # Even without app, create a ContextTask that will use stored app or create one
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context"""
            def __call__(self, *args, **kwargs):
                # Try to get app from stored reference first
                app_to_use = _flask_app
                
                if not app_to_use:
                    # Try to import and create app
                    try:
                        # Try different import paths
                        try:
                            from app import create_app
                        except ImportError:
                            # If running from celery_worker, app might already be imported
                            import sys
                            if 'app' in sys.modules:
                                app_module = sys.modules['app']
                                create_app = app_module.create_app
                            else:
                                raise
                        app_to_use = create_app()
                    except Exception as e:
                        import logging
                        logging.error(f"Failed to create Flask app in Celery task: {e}")
                        import traceback
                        logging.error(traceback.format_exc())
                        raise RuntimeError(f"Flask application context is required but app could not be created: {e}")
                
                # Use app context
                with app_to_use.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Create celery instance (will be initialized with app later)
celery = make_celery()

# Import tasks to register them with Celery
# This must be done after celery is created so tasks are registered
try:
    # Import task modules to register them
    import tasks.scanner
    import tasks.collector
except ImportError as e:
    # Tasks may not be available during initial setup
    import logging
    logging.warning(f"Could not import tasks: {e}")

