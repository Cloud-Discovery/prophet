# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Data import API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
import pandas as pd
import io

from models import Host, db
from utils.decorators import validate_json

bp = Blueprint('import', __name__)


@bp.route('/csv/hosts', methods=['POST'])
@jwt_required()
def import_hosts_from_csv():
    """Import hosts from CSV file"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': 'No file selected'}), 400
    
    user_id = get_current_user_id()
    
    try:
        # Read CSV
        df = pd.read_csv(file, keep_default_na=False)
        
        # Validate required columns
        required_columns = ['ip']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return jsonify({
                'code': 400,
                'message': f'Missing required columns: {", ".join(missing)}'
            }), 400
        
        created = []
        updated = []
        restored = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                ip = row.get('ip', '').strip()
                if not ip:
                    continue
                
                # Check if host exists (including deleted ones)
                # First check for non-deleted host
                existing = Host.query.filter_by(ip=ip, deleted_at=None).first()
                
                if existing:
                    # Update existing non-deleted host
                    if 'hostname' in df.columns:
                        existing.hostname = row.get('hostname', '') or None
                    if 'mac' in df.columns:
                        existing.mac = row.get('mac', '') or None
                    if 'vendor' in df.columns:
                        existing.vendor = row.get('vendor', '') or None
                    if 'os' in df.columns:
                        existing.os_type = row.get('os', '') or None
                    if 'version' in df.columns:
                        existing.os_version = row.get('version', '') or None
                    updated.append(existing)
                else:
                    # Check if there's a deleted host with same IP
                    deleted_host = Host.query.filter(
                        Host.ip == ip,
                        Host.deleted_at.isnot(None)
                    ).first()
                    
                    if deleted_host:
                        # Restore deleted host
                        deleted_host.deleted_at = None
                        if 'hostname' in df.columns:
                            deleted_host.hostname = row.get('hostname', '') or None
                        if 'mac' in df.columns:
                            deleted_host.mac = row.get('mac', '') or None
                        if 'vendor' in df.columns:
                            deleted_host.vendor = row.get('vendor', '') or None
                        if 'os' in df.columns:
                            deleted_host.os_type = row.get('os', '') or None
                        if 'version' in df.columns:
                            deleted_host.os_version = row.get('version', '') or None
                        restored.append(deleted_host)
                    else:
                        # Create new host
                        host = Host(
                            ip=ip,
                            hostname=row.get('hostname', '') or None if 'hostname' in df.columns else None,
                            mac=row.get('mac', '') or None if 'mac' in df.columns else None,
                            vendor=row.get('vendor', '') or None if 'vendor' in df.columns else None,
                            os_type=row.get('os', '') or None if 'os' in df.columns else None,
                            os_version=row.get('version', '') or None if 'version' in df.columns else None,
                            device_type='host',
                            is_physical=True,
                            created_by=user_id,
                        )
                        db.session.add(host)
                        created.append(host)
                    
            except Exception as e:
                # Rollback this transaction to allow other rows to continue
                db.session.rollback()
                errors.append({
                    'row': idx + 1,
                    'ip': row.get('ip', 'unknown'),
                    'error': str(e)
                })
                continue
        
        # Commit all successful operations
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to commit changes: {str(e)}")
        
        return jsonify({
            'code': 200,
            'message': f'Import completed: {len(created)} created, {len(updated)} updated, {len(restored)} restored, {len(errors)} errors',
            'data': {
                'created': len(created),
                'updated': len(updated),
                'restored': len(restored),
                'errors': errors
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 400,
            'message': f'Failed to import CSV: {str(e)}'
        }), 400

