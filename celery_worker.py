# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Celery worker entry point with Flask app context"""

# Import app module first to ensure it's available
import app

# Create Flask app instance
app_instance = app.create_app()

# Import celery_app and initialize with app
from celery_app import make_celery

# Initialize Celery with app - this will store the app reference
celery = make_celery(app_instance)

# Import tasks to register them with Celery
# This must be done after celery is initialized
import tasks.scanner
import tasks.collector

# Export celery for use with: celery -A celery_worker.celery worker
__all__ = ['celery', 'app_instance']

