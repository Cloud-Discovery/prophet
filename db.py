# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Database initialization"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to register them
        try:
            from models import (
                User, Host, HostCredential, HostDetail, HostTag, HostTagRelation,
                HostDisk, HostPartition, HostNetworkInterface, HostRelationship,
                VirtualizationPlatform, Application, ApplicationHost,
                ScanTask, CollectionTask, SystemConfig, AuditLog
            )
        except ImportError:
            # Models will be imported when needed
            pass
        
        # Create all tables
        db.create_all()
        
        # Initialize default system config
        init_default_config()
    
    return db


def init_default_config():
    """Initialize default system configuration"""
    try:
        from models import SystemConfig
        from config import Config
        
        defaults = [
            ('default_scan_concurrent', str(Config.DEFAULT_SCAN_CONCURRENT)),
            ('default_collect_concurrent', str(Config.DEFAULT_COLLECT_CONCURRENT)),
        ]
        
        for key, value in defaults:
            if not SystemConfig.query.filter_by(key=key).first():
                config = SystemConfig(key=key, value=value, description=f'Default {key}')
                db.session.add(config)
        
        db.session.commit()
    except Exception as e:
        # Ignore errors during initialization
        print(f"Warning: Failed to initialize default config: {e}")

