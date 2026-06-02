# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""System config API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import SystemConfig, db
from utils.decorators import validate_json

bp = Blueprint('config', __name__)


@bp.route('/concurrent', methods=['GET'])
@jwt_required()
def get_concurrent_config():
    """Get concurrent configuration"""
    scan_config = SystemConfig.query.filter_by(key='default_scan_concurrent').first()
    collect_config = SystemConfig.query.filter_by(key='default_collect_concurrent').first()
    
    return jsonify({
        'code': 200,
        'data': {
            'scan_concurrent': int(scan_config.value) if scan_config else 1,
            'collect_concurrent': int(collect_config.value) if collect_config else 5
        }
    })


@bp.route('/concurrent', methods=['PUT'])
@jwt_required()
@validate_json(['scan_concurrent', 'collect_concurrent'])
def update_concurrent_config():
    """Update concurrent configuration"""
    data = request.json
    
    # Update scan concurrent
    scan_config = SystemConfig.query.filter_by(key='default_scan_concurrent').first()
    if scan_config:
        scan_config.value = str(data['scan_concurrent'])
    else:
        scan_config = SystemConfig(
            key='default_scan_concurrent',
            value=str(data['scan_concurrent']),
            description='Default concurrent limit for scan tasks'
        )
        db.session.add(scan_config)
    
    # Update collect concurrent
    collect_config = SystemConfig.query.filter_by(key='default_collect_concurrent').first()
    if collect_config:
        collect_config.value = str(data['collect_concurrent'])
    else:
        collect_config = SystemConfig(
            key='default_collect_concurrent',
            value=str(data['collect_concurrent']),
            description='Default concurrent limit for collection tasks'
        )
        db.session.add(collect_config)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Configuration updated',
        'data': {
            'scan_concurrent': int(scan_config.value),
            'collect_concurrent': int(collect_config.value)
        }
    })

