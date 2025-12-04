"""
Authentication routes.
Handles user registration, login, logout, and session management.
"""

from flask import Blueprint, request, session, jsonify
from models import UserModel
from middlewares import login_required, guest_only
from utils import validate_email, validate_password

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@guest_only
def register():
    """
    Register a new user.
    
    Request Body:
        Email: str - User's email address
        PlainPassword: str - Plain text password
        
    Returns:
        201: User created successfully
        400: Validation error or email already exists
    """
    data = request.get_json()
    email = data.get('Email')
    plain_password = data.get('PlainPassword')
    
    # Validate email
    is_valid, error_msg = validate_email(email)
    if not is_valid:
        return jsonify({"message": error_msg}), 400
    
    # Validate password
    is_valid, error_msg = validate_password(plain_password)
    if not is_valid:
        return jsonify({"message": error_msg}), 400
    
    # Check if email already exists
    if UserModel.objects(Email=email).first():
        return jsonify({"message": "Email already exists"}), 400
    
    # Create and save new user
    new_user = UserModel.create_user(email, plain_password)
    new_user.save()
    
    return jsonify({
        "message": "User registered successfully",
        "user": {
            "UserID": str(new_user.UserID),
            "Email": email,
            "Role": new_user.Role
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and create session.
    
    Request Body:
        Email: str - User's email address
        PlainPassword: str - Plain text password
        
    Returns:
        200: Login successful
        401: Invalid credentials
    """
    data = request.get_json()
    email = data.get('Email')
    plain_password = data.get('PlainPassword')
    
    # Find user by email
    user = UserModel.objects(Email=email).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Verify password
    if not user.check_password(plain_password):
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Create session
    session['UserID'] = str(user.UserID)
    session['Email'] = email
    session['Role'] = user.Role
    session.permanent = True
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "UserID": str(user.UserID),
            "Email": email,
            "Role": user.Role
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout user and clear session.
    
    Returns:
        200: Logout successful
    """
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Get current authenticated user information.
    
    Returns:
        200: User information
    """
    return jsonify({
        "user": {
            "UserID": session['UserID'],
            "Email": session['Email'],
            "Role": session['Role']
        }
    }), 200
