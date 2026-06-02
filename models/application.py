# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Application model"""

from datetime import datetime
from db import db


class Application(db.Model):
    """Application model"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    graph_layout = db.Column(db.JSON, nullable=True)
    
    # Relationships
    hosts = db.relationship('Host', secondary='application_hosts', lazy='subquery', backref=db.backref('applications', lazy=True))
    
    def to_dict(self, include_hosts=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'graph_layout': self.graph_layout,
        }
        
        if include_hosts:
            data['hosts'] = [host.to_dict() for host in self.hosts]
            data['host_count'] = len(self.hosts)
        
        return data
    
    def __repr__(self):
        return f'<Application {self.name}>'


class ApplicationHost(db.Model):
    """Application-Host relation table"""
    __tablename__ = 'application_hosts'
    
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), primary_key=True)
    relationship_type = db.Column(db.String(50), default='member')  # member/depends_on/related_to
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

