# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Virtualization platform API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
from sqlalchemy import desc

from models import VirtualizationPlatform, Host, db
from sqlalchemy import func
from utils.encryption import encrypt_password
from utils.decorators import validate_json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('virtualization', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_platforms():
    """Get platform list"""
    platforms = VirtualizationPlatform.query.filter_by(deleted_at=None).order_by(desc(VirtualizationPlatform.created_at)).all()
    
    return jsonify({
        'code': 200,
        'data': [p.to_dict() for p in platforms]
    })


@bp.route('', methods=['POST'])
@jwt_required()
@validate_json(['name', 'type', 'host', 'username'])
def create_platform():
    """Create a new platform"""
    data = request.json
    user_id = get_current_user_id()
    
    platform = VirtualizationPlatform(
        name=data['name'],
        type=data['type'],
        host=data['host'],
        port=data.get('port', 443),
        username=data['username'],
        password_encrypted=encrypt_password(data['password']) if data.get('password') else None,
        region=data.get('region'),
        created_by=user_id,
    )
    
    if data.get('extra_config'):
        platform.set_extra_config(data['extra_config'])
    
    db.session.add(platform)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Platform created',
        'data': platform.to_dict()
    }), 201


@bp.route('/<int:platform_id>', methods=['GET'])
@jwt_required()
def get_platform(platform_id):
    """Get platform details with statistics"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    
    # Get platform statistics
    hosts = Host.query.filter_by(
        source_platform_id=platform_id,
        deleted_at=None
    ).all()
    
    # Count ESXi hosts (ESXi hosts from this platform)
    # ESXi hosts have: source_platform_id=platform_id, device_type='host', is_physical=False
    esxi_count = Host.query.filter(
        Host.source_platform_id == platform_id,
        Host.os_type == 'VMware ESXi',
        Host.is_physical == False,
        Host.deleted_at == None
    ).count()
    
    # Count VMs (VMs from this platform)
    # VMs have: virtualization_platform_id=platform_id, is_physical=False
    # We exclude ESXi hosts by checking device_type != 'host' (or device_type is NULL/None)
    # ESXi hosts have device_type='host', VMs have device_type='vm' or None
    from sqlalchemy import or_
    vm_count = Host.query.filter(
        Host.virtualization_platform_id == platform_id,
        Host.is_physical == False,
        or_(
            Host.device_type != 'host',
            Host.device_type == None
        ),
        Host.deleted_at == None
    ).count()
    
    # Calculate total resources
    total_cpu = sum(h.cpu_cores or 0 for h in hosts)
    total_memory = sum(h.memory_total or 0 for h in hosts)
    total_storage = sum(h.disk_total_size or 0 for h in hosts)
    
    platform_dict = platform.to_dict()
    platform_dict['statistics'] = {
        'esxi_count': esxi_count,
        'vm_count': vm_count,
        'total_hosts': len(hosts),
        'total_cpu_cores': total_cpu,
        'total_memory_gb': round(total_memory, 2),
        'total_storage_gb': round(total_storage, 2),
    }
    
    return jsonify({
        'code': 200,
        'data': platform_dict
    })


@bp.route('/<int:platform_id>', methods=['PUT'])
@jwt_required()
def update_platform(platform_id):
    """Update platform"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    data = request.json
    
    if 'name' in data:
        platform.name = data['name']
    if 'host' in data:
        platform.host = data['host']
    if 'port' in data:
        platform.port = data['port']
    if 'username' in data:
        platform.username = data['username']
    if 'password' in data and data['password']:
        # Only update password if it's provided and not empty
        platform.password_encrypted = encrypt_password(data['password'])
    if 'region' in data:
        platform.region = data['region']
    if 'extra_config' in data:
        platform.set_extra_config(data['extra_config'])
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Platform updated',
        'data': platform.to_dict()
    })


@bp.route('/<int:platform_id>', methods=['DELETE'])
@jwt_required()
def delete_platform(platform_id):
    """Soft delete platform"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    
    platform.deleted_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Platform deleted'
    })


@bp.route('/<int:platform_id>/test', methods=['POST'])
@jwt_required()
def test_platform(platform_id):
    """Test platform connection"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    
    # Test connection based on platform type
    try:
        if platform.type == 'vmware':
            # Get platform password
            password = platform.get_password()
            if not password:
                logger.error(f"Platform {platform.name} (ID: {platform_id}) password is not set or cannot be decrypted")
                return jsonify({
                    'code': 400,
                    'message': 'Platform password is not set or cannot be decrypted. Please update the platform credentials.'
                }), 400
            
            # Import only when needed
            from prophet.collector.hosts.vmware import VMwareCollector
            collector = VMwareCollector(
                ip=platform.host,
                username=platform.username,
                password=password,
                ssh_port=platform.port,
                key_path=None,
                output_path='/tmp',
                os_type='VMWARE',
            )
            collector.connect()
            return jsonify({
                'code': 200,
                'message': 'Connection successful',
                'data': {'connected': True}
            })
        else:
            return jsonify({
                'code': 400,
                'message': f'Platform type {platform.type} test not implemented yet'
            }), 400
    except Exception as e:
        logger.error(f"Platform connection test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 400,
            'message': f'Connection failed: {str(e)}'
        }), 400


@bp.route('/<int:platform_id>/sync', methods=['POST'])
@jwt_required()
def sync_platform(platform_id):
    """Sync platform resources to hosts (async with task tracking)"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    user_id = get_current_user_id()
    
    # Check if there's already a running sync task for this platform
    # We'll identify platform sync tasks by using negative platform_id in host_ids
    from models import CollectionTask
    from sqlalchemy import and_
    import json
    
    # Check for existing sync tasks (platform sync tasks use negative platform_id)
    existing_tasks = CollectionTask.query.filter(
        and_(
            CollectionTask.status.in_(['pending', 'running']),
            CollectionTask.created_by == user_id
        )
    ).all()
    
    # Check if any existing task is for this platform
    for task in existing_tasks:
        host_ids = task.get_host_ids()
        # Platform sync tasks use negative platform_id as first element to identify them
        if host_ids and len(host_ids) > 0 and host_ids[0] == -platform_id:
            return jsonify({
                'code': 400,
                'message': 'A sync task for this platform is already running',
                'data': {
                    'task_id': task.id,
                    'status': task.status
                }
            }), 400
    
    # Create a collection task for tracking sync progress
    # Use negative platform_id to identify platform sync tasks
    task = CollectionTask(
        concurrent_limit=1,  # Sync is sequential
        status='pending',
        created_by=user_id,
    )
    # Store negative platform_id to identify this as a platform sync task
    task.set_host_ids([-platform_id])
    db.session.add(task)
    db.session.flush()
    
    # Start async sync task
    from tasks.collector import sync_platform_resources_task
    sync_platform_resources_task.delay(task.id, platform_id)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Platform sync task created',
        'data': {
            'task_id': task.id,
            'status': task.status,
            'platform_id': platform_id
        }
    })

