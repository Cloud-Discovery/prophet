# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Collection task management API"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
from sqlalchemy import desc, and_
from datetime import datetime
import csv
import io

from models import CollectionTask, Host, HostDisk, HostPartition, HostNetworkInterface, db
from tasks.collector import collect_hosts_task
from utils.decorators import validate_json

bp = Blueprint('collections', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_collection_tasks():
    """Get collection task list with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = CollectionTask.query
    
    if status:
        # Support comma-separated status values
        status_list = [s.strip() for s in status.split(',')]
        query = query.filter(CollectionTask.status.in_(status_list))
    
    query = query.order_by(desc(CollectionTask.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Convert tasks to dict and identify platform sync tasks
    tasks_data = []
    for task in pagination.items:
        task_dict = task.to_dict()
        host_ids = task.get_host_ids()
        # Check if this is a platform sync task (first element is negative platform_id)
        if host_ids and len(host_ids) > 0 and host_ids[0] < 0:
            platform_id = -host_ids[0]
            task_dict['task_type'] = 'platform_sync'
            task_dict['platform_id'] = platform_id
            # Get platform name
            from models import VirtualizationPlatform
            platform = VirtualizationPlatform.query.get(platform_id)
            if platform:
                task_dict['platform_name'] = platform.name
        else:
            task_dict['task_type'] = 'collection'
        tasks_data.append(task_dict)
    
    return jsonify({
        'code': 200,
        'data': tasks_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_collection_task(task_id):
    """Get collection task details"""
    task = CollectionTask.query.get_or_404(task_id)
    
    return jsonify({
        'code': 200,
        'data': task.to_dict()
    })


@bp.route('/<int:task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_collection_task(task_id):
    """Cancel a running collection task"""
    task = CollectionTask.query.get_or_404(task_id)
    
    if task.status not in ['pending', 'running']:
        return jsonify({
            'code': 400,
            'message': f'Cannot cancel task with status: {task.status}'
        }), 400
    
    task.status = 'cancelled'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    
    # TODO: Actually cancel the Celery task if running
    
    return jsonify({
        'code': 200,
        'message': 'Collection task cancelled',
        'data': task.to_dict()
    })


@bp.route('/<int:task_id>/retry', methods=['POST'])
@jwt_required()
def retry_collection_task(task_id):
    """Retry a failed collection task"""
    task = CollectionTask.query.get_or_404(task_id)
    
    if task.status != 'failed':
        return jsonify({
            'code': 400,
            'message': f'Can only retry failed tasks, current status: {task.status}'
        }), 400
    
    # Reset task status
    task.status = 'pending'
    task.progress = 0
    task.completed_count = 0
    task.failed_count = 0
    task.error_message = None
    task.started_at = None
    task.completed_at = None
    db.session.commit()
    
    # Get concurrent limit
    concurrent_limit = task.concurrent_limit or 5
    
    # Start async task
    collect_hosts_task.delay(task.id, concurrent_limit)
    
    return jsonify({
        'code': 200,
        'message': 'Collection task retried',
        'data': task.to_dict()
    })


@bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_collection_task(task_id):
    """Delete a collection task"""
    task = CollectionTask.query.get_or_404(task_id)
    
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
        'message': 'Collection task deleted'
    })


@bp.route('/<int:task_id>/results', methods=['GET'])
@jwt_required()
def get_collection_results(task_id):
    """Get collection task results (hosts with collection data)"""
    task = CollectionTask.query.get_or_404(task_id)
    
    # Get host IDs from task
    host_ids = task.get_host_ids()
    
    if not host_ids:
        return jsonify({
            'code': 200,
            'data': []
        })
    
    # Filter out negative IDs (platform sync task marker) to get actual host IDs
    actual_host_ids = [hid for hid in host_ids if hid > 0]
    
    if not actual_host_ids:
        return jsonify({
            'code': 200,
            'data': []
        })
    
    # Get hosts with collection details
    hosts = Host.query.filter(
        Host.id.in_(actual_host_ids),
        Host.deleted_at == None
    ).all()
    
    # Build results with collection status and error messages
    # Use task's created_at as reference time to get only details from this task
    task_created_at = task.created_at
    
    results = []
    for host in hosts:
        host_dict = {
            'id': host.id,
            'ip': host.ip,
            'hostname': host.hostname,
            'os_type': host.os_type,
            'os_version': host.os_version,
        }
        
        # Get the latest HostDetail for this host created after task started
        from models import HostDetail
        latest_detail = HostDetail.query.filter(
            HostDetail.host_id == host.id,
            HostDetail.collected_at >= task_created_at
        ).order_by(HostDetail.collected_at.desc()).first()
        
        # Determine status based on latest detail from this task
        if latest_detail:
            if latest_detail.status == 'success':
                host_dict['collection_status'] = 'completed'
                host_dict['collection_success'] = True
                host_dict['collected_at'] = latest_detail.collected_at.isoformat() if latest_detail.collected_at else None
            elif latest_detail.status == 'failed':
                host_dict['collection_status'] = 'failed'
                host_dict['collection_success'] = False
                host_dict['error_message'] = latest_detail.error_message
                host_dict['collected_at'] = latest_detail.collected_at.isoformat() if latest_detail.collected_at else None
            else:
                host_dict['collection_status'] = 'unknown'
                host_dict['collection_success'] = None
        else:
            # No detail record yet - check host's current collection_status
            # This gives us real-time status during collection
            if task.status == 'running':
                # Task is running - check host's current status
                if host.collection_status == 'collecting':
                    host_dict['collection_status'] = 'collecting'
                    host_dict['collection_success'] = None
                elif host.collection_status == 'completed':
                    # Host completed but no detail record yet (shouldn't happen, but handle it)
                    host_dict['collection_status'] = 'completed'
                    host_dict['collection_success'] = True
                elif host.collection_status == 'failed':
                    host_dict['collection_status'] = 'failed'
                    host_dict['collection_success'] = False
                    # Try to get any error message
                    any_failed_detail = HostDetail.query.filter_by(
                        host_id=host.id,
                        status='failed'
                    ).order_by(HostDetail.collected_at.desc()).first()
                    if any_failed_detail and any_failed_detail.error_message:
                        host_dict['error_message'] = any_failed_detail.error_message
                else:
                    host_dict['collection_status'] = 'pending'
                    host_dict['collection_success'] = None
            else:
                # Task completed/failed - check final status
                if host.collection_status == 'completed':
                    host_dict['collection_status'] = 'completed'
                    host_dict['collection_success'] = True
                elif host.collection_status == 'failed':
                    host_dict['collection_status'] = 'failed'
                    host_dict['collection_success'] = False
                    # Try to get any error message
                    any_failed_detail = HostDetail.query.filter_by(
                        host_id=host.id,
                        status='failed'
                    ).order_by(HostDetail.collected_at.desc()).first()
                    if any_failed_detail and any_failed_detail.error_message:
                        host_dict['error_message'] = any_failed_detail.error_message
                else:
                    host_dict['collection_status'] = 'pending'
                    host_dict['collection_success'] = None
        
        results.append(host_dict)
    
    return jsonify({
        'code': 200,
        'data': results
    })


@bp.route('/<int:task_id>/export/csv', methods=['GET'])
@jwt_required()
def export_collection_results(task_id):
    """Export collection results as CSV or Excel"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        task = CollectionTask.query.get_or_404(task_id)
        export_format = request.args.get('format', 'csv').lower()
        
        # Get host IDs from task
        host_ids = task.get_host_ids()
        logger.info(f"Export task {task_id}: host_ids = {host_ids}")
        
        if not host_ids:
            return jsonify({
                'code': 404,
                'message': 'No hosts in this collection task'
            }), 404
        
        # Filter out negative IDs (platform sync task marker) to get actual host IDs
        actual_host_ids = [hid for hid in host_ids if hid > 0]
        logger.info(f"Export task {task_id}: actual_host_ids = {actual_host_ids}")
        
        if not actual_host_ids:
            return jsonify({
                'code': 404,
                'message': 'No hosts in this collection task'
            }), 404
        
        # Get hosts with all details (load network_interfaces relationship)
        from sqlalchemy.orm import selectinload
        hosts = Host.query.options(
            selectinload(Host.network_interfaces)
        ).filter(
            Host.id.in_(actual_host_ids),
            Host.deleted_at == None
        ).all()
        
        logger.info(f"Export task {task_id}: found {len(hosts)} hosts")
        
        # Debug: check if hosts are loaded
        if not hosts:
            return jsonify({
                'code': 404,
                'message': 'No hosts found for this collection task'
            }), 404
        
        if export_format == 'csv':
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            header = [
                'Platform Type', 'Hostname', 'IP', 'MAC', 'OS Type', 'OS Version', 'OS Bit',
                'OS Kernel', 'Boot Type', 'CPU Info', 'CPU Cores', 'Memory (GB)', 'Free Memory (GB)',
                'Disk Count', 'Total Disk Size (GB)', 'Network Count', 'Virtualization Type', 'Virtualization Version',
                'Collection Status', 'Last Collected At'
            ]
            writer.writerow(header)
            
            # Write data
            for host in hosts:
                # Get default network interface
                default_nic = None
                if host.network_interfaces:
                    default_nic = next((nic for nic in host.network_interfaces if nic.is_default), None)
                    if not default_nic and host.network_interfaces:
                        default_nic = host.network_interfaces[0]
                
                # Get MAC address from network interface or host
                mac_address = ''
                if default_nic and default_nic.macaddress:
                    mac_address = default_nic.macaddress
                elif host.mac:
                    mac_address = host.mac
                
                # Determine platform type
                platform_type = 'Physical'
                if host.vt_platform:
                    platform_type = host.vt_platform
                elif host.is_physical is False:
                    platform_type = 'Virtual'
                
                row = [
                    platform_type,
                    host.hostname or '',
                    host.ip or '',
                    mac_address or '',
                    host.os_type or '',
                    host.os_version or '',
                    host.os_bit or '',
                    host.os_kernel or '',
                    host.boot_type or '',
                    host.cpu_info or '',
                    host.cpu_cores if host.cpu_cores is not None else 0,
                    host.memory_total if host.memory_total is not None else 0,
                    host.memory_free if host.memory_free is not None else 0,
                    host.disk_count if host.disk_count is not None else 0,
                    host.disk_total_size if host.disk_total_size is not None else 0,
                    host.network_count if host.network_count is not None else 0,
                    host.vt_platform or '',
                    host.vt_platform_ver or '',
                    host.collection_status or 'not_collected',
                    host.last_collected_at.isoformat() if host.last_collected_at else '',
                ]
                writer.writerow(row)
            
            csv_content = output.getvalue()
            logger.info(f"Export task {task_id}: CSV content length = {len(csv_content)}, first 200 chars = {csv_content[:200]}")
            
            response = Response(
                csv_content,
                mimetype='text/csv; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename=collection_task_{task_id}_results.csv'
                }
            )
            return response
        else:
            # For Excel export, would need openpyxl or xlsxwriter
            return jsonify({
                'code': 400,
                'message': 'Excel export not implemented yet, use format=csv'
            }), 400
    except Exception as e:
        logger.error(f"Export task {task_id} failed: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'Export failed: {str(e)}'
        }), 500

