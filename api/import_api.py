# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Data import API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
import pandas as pd
import io
import ipaddress

from api.hosts import HOST_IMPORT_TEMPLATE_COLUMNS
from models import Host, HostCredential, HostTag, db
from utils.encryption import encrypt_password

bp = Blueprint('import', __name__)

COLUMN_KEY_MAP = {column['key'].lower(): column['key'] for column in HOST_IMPORT_TEMPLATE_COLUMNS}
REQUIRED_COLUMNS = [column['key'] for column in HOST_IMPORT_TEMPLATE_COLUMNS if column.get('required')]
COLUMN_ALIASES = {
    'os': 'os_type',
    'os类型': 'os_type',
    'version': 'os_version',
    'os版本': 'os_version',
}
TRUTHY_VALUES = {'true', 'yes', 'y', '1', '是'}
FALSY_VALUES = {'false', 'no', 'n', '0', '否'}


def _normalize_string(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value).strip() or None


def _parse_boolean(value):
    normalized = _normalize_string(value)
    if normalized is None:
        return None
    lower_value = normalized.lower()
    if lower_value in TRUTHY_VALUES:
        return True
    if lower_value in FALSY_VALUES:
        return False
    return None


def _parse_int(value):
    normalized = _normalize_string(value)
    if normalized is None:
        return None
    try:
        return int(float(normalized))
    except (ValueError, TypeError):
        return None


def _split_tags(value):
    normalized = _normalize_string(value)
    if normalized is None:
        return []
    return [part.strip() for part in normalized.split(',') if part.strip()]


@bp.route('/csv/hosts/metadata', methods=['GET'])
@jwt_required()
def get_hosts_import_metadata():
    """Return import template metadata for CSV uploads"""
    return jsonify({
        'code': 200,
        'data': {
            'columns': HOST_IMPORT_TEMPLATE_COLUMNS
        }
    })


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
        # Read CSV with encoding fallbacks
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({'code': 400, 'message': 'CSV file is empty'}), 400

        encoding_candidates = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'latin-1']
        df = None
        used_encoding = None
        for encoding in encoding_candidates:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), keep_default_na=False, encoding=encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            return jsonify({
                'code': 400,
                'message': 'Failed to decode CSV file. Please use UTF-8 or GBK encoding.'
            }), 400
        
        if df.empty:
            return jsonify({
                'code': 400,
                'message': 'CSV file is empty'
            }), 400
        
        # Normalize column names
        renamed_columns = {}
        for column in df.columns:
            column_name = str(column).strip()
            lower_name = column_name.lower()
            if lower_name in COLUMN_ALIASES:
                renamed_columns[column] = COLUMN_ALIASES[lower_name]
            elif lower_name in COLUMN_KEY_MAP:
                renamed_columns[column] = COLUMN_KEY_MAP[lower_name]
            else:
                renamed_columns[column] = lower_name
        df = df.rename(columns=renamed_columns)
        
        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            return jsonify({
                'code': 400,
                'message': f'Missing required columns: {", ".join(missing)}'
            }), 400
        
        created_count = 0
        updated_count = 0
        errors = []
        seen_ips = set()
        tag_cache = {}
        
        for idx, row in df.iterrows():
            row_number = idx + 2  # account for header row (header is line 1)
            try:
                ip = _normalize_string(row.get('ip', ''))
                if not ip:
                    continue
                
                if ip in seen_ips:
                    errors.append({
                        'row': row_number,
                        'ip': ip,
                        'error': 'Duplicate IP in import file'
                    })
                    continue
                
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    errors.append({
                        'row': row_number,
                        'ip': ip,
                        'error': 'Invalid IP address'
                    })
                    continue
                
                seen_ips.add(ip)
                
                normalized_data = {}
                for column in df.columns:
                    if column == 'ip':
                        continue
                    normalized_data[column] = _normalize_string(row.get(column, None))
                
                is_physical_value = None
                if 'is_physical' in df.columns:
                    is_physical_raw = row.get('is_physical', None)
                    is_physical_value = _parse_boolean(is_physical_raw)
                    if is_physical_value is None and _normalize_string(is_physical_raw) not in (None, ''):
                        errors.append({
                            'row': row_number,
                            'ip': ip,
                            'error': 'Invalid value for is_physical'
                        })
                        continue
                
                ssh_port_value = None
                if 'ssh_port' in df.columns:
                    ssh_port_value = _parse_int(row.get('ssh_port', None))
                    if ssh_port_value is not None and not (1 <= ssh_port_value <= 65535):
                        errors.append({
                            'row': row_number,
                            'ip': ip,
                            'error': 'SSH port must be between 1 and 65535'
                        })
                        continue
                
                tag_names = _split_tags(row.get('tags', None)) if 'tags' in df.columns else []
                if tag_names:
                    tag_names = list(dict.fromkeys(tag_names))
                credential_columns_present = any(col in df.columns for col in ['username', 'password', 'ssh_port', 'key_path'])
                username_value = normalized_data.get('username')
                password_value = _normalize_string(row.get('password', None))
                key_path_value = normalized_data.get('key_path')
                
                existing = Host.query.filter_by(ip=ip, deleted_at=None).first()
                
                if existing:
                    if credential_columns_present and (not existing.credentials) and not username_value:
                        errors.append({
                            'row': row_number,
                            'ip': ip,
                            'error': 'Username is required when creating credentials'
                        })
                        continue
                    
                    updated_flag = False
                    host_field_keys = ['hostname', 'mac', 'vendor', 'os_type', 'os_version', 'device_type', 'vt_platform', 'vt_platform_ver']
                    for field in host_field_keys:
                        if field in df.columns:
                            new_value = normalized_data.get(field)
                            if new_value != getattr(existing, field):
                                setattr(existing, field, new_value)
                                updated_flag = True
                    
                    if is_physical_value is not None and is_physical_value != existing.is_physical:
                        existing.is_physical = is_physical_value
                        updated_flag = True
                    
                    if 'tags' in df.columns:
                        tag_instances = []
                        for tag_name in tag_names:
                            cache_key = tag_name.lower()
                            if cache_key in tag_cache:
                                tag = tag_cache[cache_key]
                            else:
                                tag = HostTag.query.filter_by(name=tag_name).first()
                                if not tag:
                                    tag = HostTag(name=tag_name)
                                    db.session.add(tag)
                                    db.session.flush()
                                tag_cache[cache_key] = tag
                            tag_instances.append(tag)
                        existing.tags = tag_instances
                        updated_flag = True
                    
                    if credential_columns_present:
                        credential = existing.credentials[0] if existing.credentials else None
                        if not credential:
                            credential = HostCredential(
                                host_id=existing.id,
                                username=username_value,
                                ssh_port=ssh_port_value or 22
                            )
                            db.session.add(credential)
                            updated_flag = True
                        
                        if username_value and credential.username != username_value:
                            credential.username = username_value
                            updated_flag = True
                        if password_value:
                            credential.password_encrypted = encrypt_password(password_value)
                            updated_flag = True
                        if ssh_port_value is not None and credential.ssh_port != ssh_port_value:
                            credential.ssh_port = ssh_port_value
                            updated_flag = True
                        if 'key_path' in df.columns and credential.key_path != key_path_value:
                            credential.key_path = key_path_value
                            updated_flag = True
                    
                    if updated_flag:
                        updated_count += 1
                else:
                    if credential_columns_present and not username_value:
                        errors.append({
                            'row': row_number,
                            'ip': ip,
                            'error': 'Username is required when creating credentials'
                        })
                        continue
                    
                    host = Host(
                        ip=ip,
                        hostname=normalized_data.get('hostname'),
                        mac=normalized_data.get('mac'),
                        vendor=normalized_data.get('vendor'),
                        os_type=normalized_data.get('os_type'),
                        os_version=normalized_data.get('os_version'),
                        device_type=normalized_data.get('device_type') or 'host',
                        is_physical=True if is_physical_value is None else is_physical_value,
                        vt_platform=normalized_data.get('vt_platform'),
                        vt_platform_ver=normalized_data.get('vt_platform_ver'),
                        source='manual',
                        collection_status='not_collected',
                        created_by=user_id,
                    )
                    db.session.add(host)
                    db.session.flush()
                    created_count += 1
                    
                    if 'tags' in df.columns:
                        tag_instances = []
                        for tag_name in tag_names:
                            cache_key = tag_name.lower()
                            if cache_key in tag_cache:
                                tag = tag_cache[cache_key]
                            else:
                                tag = HostTag.query.filter_by(name=tag_name).first()
                                if not tag:
                                    tag = HostTag(name=tag_name)
                                    db.session.add(tag)
                                    db.session.flush()
                                tag_cache[cache_key] = tag
                            tag_instances.append(tag)
                        host.tags = tag_instances
                    
                    if credential_columns_present:
                        credential = HostCredential(
                            host_id=host.id,
                            username=username_value,
                            ssh_port=ssh_port_value or 22,
                            key_path=key_path_value
                        )
                        if password_value:
                            credential.password_encrypted = encrypt_password(password_value)
                        db.session.add(credential)
            
            except Exception as e:
                errors.append({
                    'row': row_number,
                    'ip': row.get('ip', 'unknown'),
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'Import completed: {created_count} created, {updated_count} updated, {len(errors)} errors',
            'data': {
                'created': created_count,
                'updated': updated_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 400,
            'message': f'Failed to import CSV: {str(e)}'
        }), 400

