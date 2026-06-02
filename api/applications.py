# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Applications API"""

import json

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required
from utils.jwt import get_current_user_id
from sqlalchemy import desc, or_

from models import Application, ApplicationHost, Host, HostRelationship, db
from utils.decorators import validate_json
from datetime import datetime

bp = Blueprint('applications', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_applications():
    """Get application list"""
    applications = Application.query.filter_by(deleted_at=None).order_by(desc(Application.created_at)).all()
    
    return jsonify({
        'code': 200,
        'data': [app.to_dict(include_hosts=True) for app in applications]
    })


@bp.route('', methods=['POST'])
@jwt_required()
@validate_json(['name'])
def create_application():
    """Create a new application"""
    data = request.json
    user_id = get_current_user_id()
    
    application = Application(
        name=data['name'],
        description=data.get('description'),
        created_by=user_id,
    )
    
    db.session.add(application)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Application created',
        'data': application.to_dict()
    }), 201


@bp.route('/<int:app_id>', methods=['GET'])
@jwt_required()
def get_application(app_id):
    """Get application details"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    
    return jsonify({
        'code': 200,
        'data': application.to_dict(include_hosts=True)
    })


@bp.route('/<int:app_id>', methods=['PUT'])
@jwt_required()
def update_application(app_id):
    """Update application"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    data = request.json
    
    if 'name' in data:
        application.name = data['name']
    if 'description' in data:
        application.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Application updated',
        'data': application.to_dict()
    })


@bp.route('/<int:app_id>', methods=['DELETE'])
@jwt_required()
def delete_application(app_id):
    """Soft delete application"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    
    application.deleted_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Application deleted'
    })


@bp.route('/<int:app_id>/hosts', methods=['POST'])
@jwt_required()
@validate_json(['host_ids'])
def add_hosts_to_application(app_id):
    """Add hosts to application"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    data = request.json
    host_ids = data['host_ids']
    relationship_type = data.get('relationship_type', 'member')
    
    for host_id in host_ids:
        host = Host.query.filter_by(id=host_id, deleted_at=None).first()
        if not host:
            continue
        
        # Check if relation exists
        existing = ApplicationHost.query.filter_by(
            application_id=app_id,
            host_id=host_id
        ).first()
        
        if not existing:
            relation = ApplicationHost(
                application_id=app_id,
                host_id=host_id,
                relationship_type=relationship_type
            )
            db.session.add(relation)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Hosts added to application',
        'data': application.to_dict(include_hosts=True)
    })


@bp.route('/<int:app_id>/hosts/<int:host_id>', methods=['DELETE'])
@jwt_required()
def remove_host_from_application(app_id, host_id):
    """Remove a host from application"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    
    relation = ApplicationHost.query.filter_by(application_id=app_id, host_id=host_id).first()
    if not relation:
        return jsonify({
            'code': 404,
            'message': 'Host is not associated with the application'
        }), 404
    
    db.session.delete(relation)
    db.session.flush()
    
    remaining_host_ids = {
        ah.host_id for ah in ApplicationHost.query.filter_by(application_id=app_id).all()
    }
    
    host_relationships = HostRelationship.query.filter(
        or_(
            HostRelationship.from_host_id == host_id,
            HostRelationship.to_host_id == host_id
        )
    ).all()
    
    for relation in host_relationships:
        if (relation.from_host_id not in remaining_host_ids and
                relation.to_host_id not in remaining_host_ids):
            db.session.delete(relation)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Host removed from application',
        'data': application.to_dict(include_hosts=True)
    })


def _build_default_graph_payload(application: Application):
    """Construct a default graph payload from current application data."""
    host_ids = [h.id for h in application.hosts]

    relationships = HostRelationship.query.filter(
        HostRelationship.from_host_id.in_(host_ids),
        HostRelationship.to_host_id.in_(host_ids)
    ).all()

    nodes = []
    for host in application.hosts:
        nodes.append({
            'id': host.id,
            'label': host.hostname or host.ip or f'Host {host.id}',
            'type': host.device_type or 'host',
            'bindingHostId': host.id,
            'data': {
                'ip': host.ip,
                'hostname': host.hostname,
                'device_type': host.device_type,
                'os_type': host.os_type,
                'is_physical': host.is_physical,
                'tags': [tag.to_dict() for tag in host.tags]
            }
        })

    edge_palette = {
        'depends_on': '#2563EB',
        'connects_to': '#0EA5E9',
        'runs_on': '#10B981',
        'member': '#6B7280'
    }

    edges = []
    for relation in relationships:
        edges.append({
            'id': relation.id,
            'source': relation.from_host_id,
            'target': relation.to_host_id,
            'relationshipType': relation.relationship_type,
            'label': relation.relationship_type,
            'description': relation.description or '',
            'style': {
                'color': edge_palette.get(relation.relationship_type, '#6B7280')
            }
        })

    return {
        'nodes': nodes,
        'edges': edges,
        'resourceNodes': [],
        'metadata': {
            'generated_at': datetime.utcnow().isoformat()
        }
    }


@bp.route('/<int:app_id>/graph', methods=['GET'])
@jwt_required()
def get_application_graph(app_id):
    """Get application relationship graph"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    payload = application.graph_layout or _build_default_graph_payload(application)

    return jsonify({
        'code': 200,
        'data': payload
    })


@bp.route('/<int:app_id>/graph', methods=['PUT'])
@jwt_required()
def save_application_graph(app_id):
    """Persist custom application graph layout."""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    data = request.get_json(silent=True) or {}

    nodes = data.get('nodes')
    edges = data.get('edges')
    resource_nodes = data.get('resourceNodes', [])
    metadata = data.get('metadata', {})

    if not isinstance(nodes, list) or not isinstance(edges, list):
        return jsonify({
            'code': 400,
            'message': 'nodes and edges must be provided as arrays'
        }), 400

    metadata['saved_at'] = datetime.utcnow().isoformat()
    metadata['saved_by'] = get_current_user_id()

    application.graph_layout = {
        'nodes': nodes,
        'edges': edges,
        'resourceNodes': resource_nodes,
        'metadata': metadata
    }
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': 'Graph layout saved'
    })


@bp.route('/<int:app_id>/graph/export', methods=['GET'])
@jwt_required()
def export_application_graph(app_id):
    """Export the application graph as downloadable JSON."""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    payload = application.graph_layout or _build_default_graph_payload(application)

    json_body = json.dumps(payload, ensure_ascii=False, indent=2)

    response = make_response(json_body)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=application-{app_id}-graph.json'
    return response


@bp.route('/<int:app_id>/relationships', methods=['GET'])
@jwt_required()
def get_application_relationships(app_id):
    """List relationships for an application"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    host_ids = [h.id for h in application.hosts]
    
    relationships = HostRelationship.query.filter(
        HostRelationship.from_host_id.in_(host_ids),
        HostRelationship.to_host_id.in_(host_ids)
    ).all()
    
    return jsonify({
        'code': 200,
        'data': [r.to_dict() for r in relationships]
    })


@bp.route('/<int:app_id>/relationships', methods=['POST'])
@jwt_required()
@validate_json(['from_host_id', 'to_host_id', 'relationship_type'])
def create_relationship(app_id):
    """Create host relationship"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    data = request.json
    
    # Verify hosts are in application
    host_ids = [h.id for h in application.hosts]
    if data['from_host_id'] not in host_ids or data['to_host_id'] not in host_ids:
        return jsonify({
            'code': 400,
            'message': 'Both hosts must be in the application'
        }), 400
    
    # Check if relationship exists
    existing = HostRelationship.query.filter_by(
        from_host_id=data['from_host_id'],
        to_host_id=data['to_host_id']
    ).first()
    
    if existing:
        return jsonify({
            'code': 400,
            'message': 'Relationship already exists'
        }), 400
    
    relationship = HostRelationship(
        from_host_id=data['from_host_id'],
        to_host_id=data['to_host_id'],
        relationship_type=data['relationship_type'],
        description=data.get('description')
    )
    
    db.session.add(relationship)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Relationship created',
        'data': relationship.to_dict()
    }), 201


@bp.route('/<int:app_id>/relationships/<int:relationship_id>', methods=['PUT'])
@jwt_required()
def update_relationship(app_id, relationship_id):
    """Update host relationship"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    data = request.json or {}
    
    relationship = HostRelationship.query.filter_by(id=relationship_id).first_or_404()
    
    # Ensure both hosts belong to the application
    host_ids = [h.id for h in application.hosts]
    if relationship.from_host_id not in host_ids or relationship.to_host_id not in host_ids:
        return jsonify({
            'code': 400,
            'message': 'Relationship hosts must belong to the application'
        }), 400
    
    if 'relationship_type' in data:
        relationship.relationship_type = data['relationship_type']
    if 'description' in data:
        relationship.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Relationship updated',
        'data': relationship.to_dict()
    })


@bp.route('/<int:app_id>/relationships/<int:relationship_id>', methods=['DELETE'])
@jwt_required()
def delete_relationship(app_id, relationship_id):
    """Delete host relationship"""
    application = Application.query.filter_by(id=app_id, deleted_at=None).first_or_404()
    relationship = HostRelationship.query.filter_by(id=relationship_id).first_or_404()
    
    host_ids = [h.id for h in application.hosts]
    if relationship.from_host_id not in host_ids or relationship.to_host_id not in host_ids:
        return jsonify({
            'code': 400,
            'message': 'Relationship hosts must belong to the application'
        }), 400
    
    db.session.delete(relationship)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'Relationship deleted'
    })

