"""
Authentication middleware decorators.
"""

from functools import wraps
from flask import session, jsonify


def login_required(f):
    """
    Decorator to require authentication for a route.
    Returns 401 if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "UserID" not in session:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


def guest_only(f):
    """
    Decorator to require user NOT be authenticated.
    Returns 400 if user is already logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "UserID" in session:
            return jsonify({"message": "Already logged in"}), 400
        return f(*args, **kwargs)
    return decorated_function
