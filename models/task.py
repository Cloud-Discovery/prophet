# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Task models"""

from datetime import datetime
from db import db
import json


class ScanTask(db.Model):
    """Network scan task model"""
    __tablename__ = 'scan_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    target = db.Column(db.String(255), nullable=False)  # IP range or CIDR
    status = db.Column(db.String(50), default='pending', index=True)  # pending/running/completed/failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    result_count = db.Column(db.Integer, default=0)
    current_host = db.Column(db.String(45))  # Currently scanning host
    error_message = db.Column(db.Text)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'target': self.target,
            'status': self.status,
            'progress': self.progress,
            'result_count': self.result_count,
            'current_host': self.current_host,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f'<ScanTask {self.name}>'


class CollectionTask(db.Model):
    """Host collection task model"""
    __tablename__ = 'collection_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_task_id = db.Column(db.Integer, db.ForeignKey('scan_tasks.id'), nullable=True)
    host_ids = db.Column(db.Text)  # JSON array of host IDs
    status = db.Column(db.String(50), default='pending', index=True)  # pending/running/completed/failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    concurrent_limit = db.Column(db.Integer, default=5)
    current_running = db.Column(db.Integer, default=0)
    completed_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def get_host_ids(self):
        """Get host IDs as list"""
        if self.host_ids:
            return json.loads(self.host_ids)
        return []
    
    def set_host_ids(self, host_id_list):
        """Set host IDs from list"""
        self.host_ids = json.dumps(host_id_list)
    
    def to_dict(self):
        """Convert to dictionary"""
        # Calculate total count
        host_ids = self.get_host_ids()
        # Check if this is a platform sync task (first element is negative platform_id)
        if host_ids and len(host_ids) > 0 and host_ids[0] < 0:
            # Platform sync task - count actual host IDs (excluding the negative platform_id marker)
            # Filter out negative IDs to get actual host IDs
            actual_host_ids = [hid for hid in host_ids if hid > 0]
            if actual_host_ids:
                # Use actual host count if available
                total_count = len(actual_host_ids)
            else:
                # If no actual hosts yet, estimate from progress
                total_count = None
                done = self.completed_count + self.failed_count
                if self.progress > 0 and done > 0:
                    # Estimate total from progress: done / progress = total
                    # Round up to ensure we don't show less than actual
                    estimated_total = int(done / (self.progress / 100.0))
                    # Use the larger of estimated or done (to handle rounding errors)
                    total_count = max(estimated_total, done)
                elif self.status in ['completed', 'failed'] and done > 0:
                    # If task is done, total is at least completed + failed
                    total_count = done
        else:
            # Collection task - total is from host_ids
            total_count = len(host_ids) if host_ids else 0
        
        return {
            'id': self.id,
            'scan_task_id': self.scan_task_id,
            'host_ids': host_ids,
            'status': self.status,
            'progress': self.progress,
            'concurrent_limit': self.concurrent_limit,
            'current_running': self.current_running,
            'completed_count': self.completed_count,
            'failed_count': self.failed_count,
            'total_count': total_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f'<CollectionTask {self.id}>'

