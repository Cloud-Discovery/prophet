# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Scanner API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
from sqlalchemy import desc
from datetime import datetime

from models import ScanTask, Host, db
from tasks.scanner import scan_network_task
from utils.decorators import validate_json

bp = Blueprint('scanner', __name__)


@bp.route('', methods=['POST'])
@jwt_required()
@validate_json(['name', 'target'])
def create_scan_task():
    """Create a new scan task"""
    data = request.json
    user_id = get_current_user_id()
    
    # Create scan task
    scan_task = ScanTask(
        name=data['name'],
        target=data['target'],
        status='pending',
        created_by=user_id,
    )
    
    db.session.add(scan_task)
    db.session.commit()
    
    # Start async task
    nmap_args = data.get('nmap_args', '-sS -O')
    scan_network_task.delay(scan_task.id, data['target'], nmap_args)
    
    return jsonify({
        'code': 200,
        'message': 'Scan task created',
        'data': scan_task.to_dict()
    }), 201


@bp.route('', methods=['GET'])
@jwt_required()
def get_scan_tasks():
    """Get scan task list"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = ScanTask.query
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(desc(ScanTask.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'code': 200,
        'data': [task.to_dict() for task in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_scan_task(task_id):
    """Get scan task details"""
    task = ScanTask.query.get_or_404(task_id)
    
    return jsonify({
        'code': 200,
        'data': task.to_dict()
    })


@bp.route('/<int:task_id>/results', methods=['GET'])
@jwt_required()
def get_scan_results(task_id):
    """Get scan task results (hosts found)"""
    task = ScanTask.query.get_or_404(task_id)
    
    # Get hosts by source_scan_task_id
    hosts = Host.query.filter(
        Host.source_scan_task_id == task_id,
        Host.deleted_at == None
    ).all()
    
    return jsonify({
        'code': 200,
        'data': [host.to_dict() for host in hosts]
    })


@bp.route('/<int:task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_scan_task(task_id):
    """Cancel a running scan task"""
    task = ScanTask.query.get_or_404(task_id)
    
    if task.status not in ['pending', 'running']:
        return jsonify({
            'code': 400,
            'message': f'Cannot cancel task with status: {task.status}'
        }), 400
    
    task.status = 'cancelled'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    
    # TODO: Actually cancel the Celery task if running
    # This would require storing the task ID in ScanTask model
    
    return jsonify({
        'code': 200,
        'message': 'Scan task cancelled',
        'data': task.to_dict()
    })


@bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_scan_task(task_id):
    """Delete a scan task"""
    task = ScanTask.query.get_or_404(task_id)
    
    # Only allow deleting completed, failed, or cancelled tasks
    if task.status in ['pending', 'running']:
        return jsonify({
            'code': 400,
            'message': 'Cannot delete task that is pending or running'
        }), 400
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Scan task deleted'
    })

