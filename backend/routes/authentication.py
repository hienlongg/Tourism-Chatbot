"""
Authentication routes.
Handles user registration, login, logout, Google Auth, and session management.
"""

import requests
import secrets
from flask import Blueprint, request, session, jsonify, current_app

from backend.models import UserModel
from backend.middlewares.decorators import login_required, guest_only
from backend.utils import validate_email, validate_password

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@guest_only
def register():
    """
    Register a new user.
    """
    data = request.get_json()
    
    # Handle both lowercase and capitalized field names for compatibility
    email = data.get('email') or data.get('Email')
    plain_password = data.get('plain_password') or data.get('PlainPassword')
    name = data.get('name') or data.get('Name')

    # Check if required fields are present
    if not email:
        return jsonify({"message": "Email is required"}), 400
    
    if not plain_password:
        return jsonify({"message": "Password is required"}), 400
    
    # Validate email
    is_valid, error_msg = validate_email(email)
    if not is_valid:
        return jsonify({"message": error_msg}), 400
    
    # Validate password
    is_valid, error_msg = validate_password(plain_password)
    if not is_valid:
        return jsonify({"message": error_msg}), 400
    
    # Check if email already exists
    if UserModel.objects(email=email).first():
        return jsonify({"message": "Email already exists"}), 400
    
    # Create and save new user
    try:
        # Try passing name if the model supports it
        new_user = UserModel.create_user(email, plain_password, name=name)
    except TypeError:
        # Fallback if create_user doesn't accept name
        new_user = UserModel.create_user(email, plain_password)
        
    new_user.save()
    
    return jsonify({
        "message": "User registered successfully",
        "user": {
            "user_id": str(new_user.user_id),
            "email": email,
            "role": new_user.role
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and create session.
    """
    data = request.get_json()
    email = data.get('email')
    plain_password = data.get('plain_password')
    
    # Find user by email
    user = UserModel.objects(email=email).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Verify password
    if not user.check_password(plain_password):
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Create session
    session['user_id'] = str(user.user_id)
    session['email'] = email
    session['role'] = user.role
    session.permanent = True
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id": str(user.user_id),
            "email": email,
            "role": user.role
        }
    }), 200


@auth_bp.route('/google', methods=['POST'])
def google_login():
    """
    Handle Google Login via Access Token.
    """
    data = request.get_json()
    access_token = data.get('token') # Frontend sends access_token
    
    if not access_token:
        return jsonify({"message": "Token is required"}), 400

    try:
        # 1. Use Access Token to get User Info from Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if not google_response.ok:
            return jsonify({"message": "Failed to fetch user info from Google"}), 401
            
        id_info = google_response.json()
        
        # Extract user info
        email = id_info.get('email')
        name = id_info.get('name')
        picture = id_info.get('picture')

        # 2. Check if user exists in DB
        user = UserModel.objects(email=email).first()

        if not user:
            # New user -> Create account
            random_password = secrets.token_urlsafe(16)
            
            try:
                user = UserModel.create_user(email, random_password, name=name)
            except TypeError:
                user = UserModel.create_user(email, random_password)
                
            # If your model has avatar field, set it here manually if create_user didn't
            # user.avatar = picture 
            
            user.save()

        # 3. Create Session
        session['user_id'] = str(user.user_id)
        session['email'] = email
        session['role'] = user.role
        session.permanent = True

        return jsonify({
            "message": "Google login successful",
            "user": {
                "user_id": str(user.user_id),
                "email": email,
                "role": user.role,
                "avatar": picture,
                "name": name
            }
        }), 200

    except Exception as e:
        print(f"Google Auth Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout user and clear session.
    """
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route('/me', methods=['GET'])
# Removed @login_required to allow frontend check without 401 error
def get_current_user():
    """
    Get current authenticated user information.
    """
    if 'user_id' not in session:
        # Return null user instead of 401 to keep console clean
        return jsonify({"user": None}), 200
    
    return jsonify({
        "user": {
            "user_id": session['user_id'],
            "email": session['email'],
            "role": session['role']
        }
    }), 200