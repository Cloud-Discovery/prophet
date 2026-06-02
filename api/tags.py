# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Tags API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import HostTag, HostTagRelation, Host, PlatformTagRelation, VirtualizationPlatform, db
from utils.decorators import validate_json

bp = Blueprint('tags', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_tags():
    """Get all tags"""
    tags = HostTag.query.order_by(HostTag.name).all()
    
    # Include host count for each tag
    tag_dicts = []
    for tag in tags:
        tag_dict = tag.to_dict()
        # Count hosts with this tag
        host_count = HostTagRelation.query.filter_by(tag_id=tag.id).join(Host).filter(Host.deleted_at.is_(None)).count()
        tag_dict['host_count'] = host_count
        tag_dicts.append(tag_dict)
    
    return jsonify({
        'code': 200,
        'data': tag_dicts
    })


@bp.route('', methods=['POST'])
@jwt_required()
@validate_json(['name'])
def create_tag():
    """Create a new tag"""
    data = request.json
    
    # Check if tag exists
    existing = HostTag.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'code': 400, 'message': 'Tag already exists'}), 400
    
    tag = HostTag(
        name=data['name'],
        color=data.get('color', '#3B82F6'),
        description=data.get('description'),
    )
    
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tag created',
        'data': tag.to_dict()
    }), 201


@bp.route('/<int:tag_id>', methods=['PUT'])
@jwt_required()
def update_tag(tag_id):
    """Update tag"""
    tag = HostTag.query.get_or_404(tag_id)
    data = request.json
    
    if 'name' in data:
        tag.name = data['name']
    if 'color' in data:
        tag.color = data['color']
    if 'description' in data:
        tag.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tag updated',
        'data': tag.to_dict()
    })


@bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """Delete tag"""
    tag = HostTag.query.get_or_404(tag_id)
    
    # Remove all relations
    HostTagRelation.query.filter_by(tag_id=tag_id).delete()
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tag deleted'
    })


@bp.route('/hosts/<int:host_id>', methods=['POST'])
@jwt_required()
@validate_json(['tag_ids'])
def add_host_tags(host_id):
    """Add tags to host"""
    host = Host.query.filter_by(id=host_id, deleted_at=None).first_or_404()
    data = request.json
    tag_ids = data['tag_ids']
    
    for tag_id in tag_ids:
        # Check if relation exists
        existing = HostTagRelation.query.filter_by(host_id=host_id, tag_id=tag_id).first()
        if not existing:
            relation = HostTagRelation(host_id=host_id, tag_id=tag_id)
            db.session.add(relation)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tags added',
        'data': host.to_dict()
    })


@bp.route('/hosts/<int:host_id>/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_host_tag(host_id, tag_id):
    """Remove tag from host"""
    host = Host.query.filter_by(id=host_id, deleted_at=None).first_or_404()
    
    relation = HostTagRelation.query.filter_by(host_id=host_id, tag_id=tag_id).first()
    if relation:
        db.session.delete(relation)
        db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tag removed'
    })


@bp.route('/platforms/<int:platform_id>', methods=['POST'])
@jwt_required()
@validate_json(['tag_ids'])
def add_platform_tags(platform_id):
    """Add tags to platform"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    data = request.json
    tag_ids = data['tag_ids']
    
    for tag_id in tag_ids:
        # Check if relation exists
        existing = PlatformTagRelation.query.filter_by(platform_id=platform_id, tag_id=tag_id).first()
        if not existing:
            relation = PlatformTagRelation(platform_id=platform_id, tag_id=tag_id)
            db.session.add(relation)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tags added',
        'data': platform.to_dict()
    })


@bp.route('/platforms/<int:platform_id>/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_platform_tag(platform_id, tag_id):
    """Remove tag from platform"""
    platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first_or_404()
    
    relation = PlatformTagRelation.query.filter_by(platform_id=platform_id, tag_id=tag_id).first()
    if relation:
        db.session.delete(relation)
        db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Tag removed'
    })


@bp.route('/<int:tag_id>/hosts', methods=['GET'])
@jwt_required()
def get_tag_hosts(tag_id):
    """Get hosts with a specific tag"""
    from sqlalchemy.orm import selectinload
    from flask import request
    
    tag = HostTag.query.get_or_404(tag_id)
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Limit max per_page
    
    # Query hosts with this tag
    query = Host.query.filter(
        Host.deleted_at.is_(None),
        Host.id.in_(
            db.session.query(HostTagRelation.host_id).filter_by(tag_id=tag_id)
        )
    ).options(selectinload(Host.tags))
    
    # Get search query
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Host.ip.like(f'%{search}%'),
                Host.hostname.like(f'%{search}%')
            )
        )
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get error messages for failed hosts
    host_dicts = []
    for host in pagination.items:
        host_dict = host.to_dict()
        # Add error_message from latest failed HostDetail if collection_status is 'failed'
        if host.collection_status == 'failed':
            from models import HostDetail
            latest_failed_detail = HostDetail.query.filter_by(
                host_id=host.id,
                status='failed'
            ).order_by(HostDetail.collected_at.desc()).first()
            if latest_failed_detail and latest_failed_detail.error_message:
                host_dict['error_message'] = latest_failed_detail.error_message
        host_dicts.append(host_dict)
    
    return jsonify({
        'code': 200,
        'data': host_dicts,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/<int:tag_id>/hosts/batch-remove', methods=['POST'])
@jwt_required()
@validate_json(['host_ids'])
def batch_remove_tag_hosts(tag_id):
    """Batch remove hosts from tag"""
    tag = HostTag.query.get_or_404(tag_id)
    data = request.json
    host_ids = data['host_ids']
    
    removed_count = 0
    for host_id in host_ids:
        relation = HostTagRelation.query.filter_by(host_id=host_id, tag_id=tag_id).first()
        if relation:
            db.session.delete(relation)
            removed_count += 1
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': f'Removed tag from {removed_count} host(s)',
        'data': {'removed_count': removed_count}
    })

