# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Utility decorators"""

from functools import wraps
from flask import request, jsonify


def validate_json(required_fields):
    """Validate JSON request has required fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'code': 400, 'message': 'Content-Type must be application/json'}), 400
            
            data = request.json
            missing = [field for field in required_fields if field not in data or not data[field]]
            if missing:
                return jsonify({
                    'code': 400,
                    'message': f'Missing required fields: {", ".join(missing)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

