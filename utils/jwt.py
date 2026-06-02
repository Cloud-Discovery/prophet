# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""JWT utility functions"""

from flask_jwt_extended import get_jwt_identity


def get_current_user_id():
    """Get current user ID from JWT token, converting string to int if needed"""
    user_id = get_jwt_identity()
    # JWT identity is stored as string in Flask-JWT-Extended 4.6.0+
    if isinstance(user_id, str):
        try:
            return int(user_id)
        except ValueError:
            return None
    return user_id

