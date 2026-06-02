# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Virtualization platform model"""

from datetime import datetime
from db import db
import json


class PlatformTagRelation(db.Model):
    """Platform-Tag relation table"""
    __tablename__ = 'platform_tag_relations'
    
    platform_id = db.Column(db.Integer, db.ForeignKey('virtualization_platforms.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('host_tags.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VirtualizationPlatform(db.Model):
    """Virtualization platform model"""
    __tablename__ = 'virtualization_platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False, index=True)  # vmware/openstack/aliyun/huawei
    
    # Connection info
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=443)
    username = db.Column(db.String(255), nullable=False)
    password_encrypted = db.Column(db.Text)  # Encrypted password
    
    # Platform-specific config
    region = db.Column(db.String(100))  # For cloud platforms
    extra_config = db.Column(db.Text)  # JSON string for platform-specific config
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationships
    tags = db.relationship('HostTag', secondary='platform_tag_relations', lazy='subquery', backref=db.backref('platforms', lazy=True))
    
    def get_extra_config(self):
        """Get extra config as dict"""
        if self.extra_config:
            return json.loads(self.extra_config)
        return {}
    
    def set_extra_config(self, config_dict):
        """Set extra config from dict"""
        self.extra_config = json.dumps(config_dict, ensure_ascii=False)
    
    def get_password(self):
        """Get decrypted password"""
        if not self.password_encrypted:
            return None
        
        from utils.encryption import decrypt_password
        try:
            decrypted = decrypt_password(self.password_encrypted)
            # Ensure we return a non-empty string
            return decrypted if decrypted else None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to decrypt password for platform {self.id}: {e}")
            return None
    
    def to_dict(self, decrypt_password=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'region': self.region,
            'extra_config': self.get_extra_config(),
            'tags': [tag.to_dict() for tag in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if decrypt_password:
            data['password'] = self.get_password()
        
        return data
    
    def __repr__(self):
        return f'<VirtualizationPlatform {self.name}>'

