"""
Authentication routes.
Handles user registration, login, logout, Google Auth, and session management.
"""

import requests
import secrets
from flask import Blueprint, request, session, jsonify
from backend.models import UserModel
from backend.middlewares.decorators import login_required, guest_only
from backend.utils import validate_email, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@guest_only
def register():
    data = request.get_json()
    email = data.get('email') or data.get('Email')
    plain_password = data.get('plain_password') or data.get('PlainPassword')
    name = data.get('name') or data.get('Name')

    if not email or not plain_password:
        return jsonify({"message": "Email and Password are required"}), 400
    
    is_valid, error_msg = validate_email(email)
    if not is_valid: return jsonify({"message": error_msg}), 400
    
    is_valid, error_msg = validate_password(plain_password)
    if not is_valid: return jsonify({"message": error_msg}), 400
    
    if UserModel.objects(email=email).first():
        return jsonify({"message": "Email already exists"}), 400
    
    # Tạo user mới (Hàm create_user giờ đã nhận tham số name)
    new_user = UserModel.create_user(email, plain_password, name=name)
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
    data = request.get_json()
    email = data.get('email')
    plain_password = data.get('plain_password')
    
    user = UserModel.objects(email=email).first()
    if not user or not user.check_password(plain_password):
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
            "role": user.role,
            "avatar": getattr(user, 'avatar', None), # Trả về avatar nếu có
            "name": getattr(user, 'name', None)
        }
    }), 200

@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Handle Google Login via Access Token."""
    data = request.get_json()
    access_token = data.get('token')
    
    if not access_token:
        return jsonify({"message": "Token is required"}), 400

    try:
        # 1. Lấy thông tin từ Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if not google_response.ok:
            return jsonify({"message": "Failed to fetch user info from Google"}), 401
            
        id_info = google_response.json()
        email = id_info.get('email')
        name = id_info.get('name')
        picture = id_info.get('picture') # Link ảnh Google

        # 2. Check user tồn tại
        user = UserModel.objects(email=email).first()

        if not user:
            # Tạo user mới
            random_password = secrets.token_urlsafe(16)
            user = UserModel.create_user(email, random_password, name=name)
        
        # 👇 CẬP NHẬT AVATAR VÀO DB
        user.avatar = picture
        if name: user.name = name # Cập nhật tên nếu có
        user.save()

        # 3. Tạo Session
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
                "avatar": user.avatar, 
                "name": user.name
            }
        }), 200

    except Exception as e:
        print(f"Google Auth Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user information."""
    if 'user_id' not in session:
        return jsonify({"user": None}), 200
    
    try:
        # Query lại DB để lấy avatar mới nhất
        user = UserModel.objects(pk=session['user_id']).first()
    except Exception:
        user = None
    
    # 👇 KHAI BÁO BIẾN TRƯỚC KHI DÙNG (Fix NameError)
    avatar_url = getattr(user, 'avatar', None) if user else None
    user_name = getattr(user, 'name', None) if user else None
    
    return jsonify({
        "user": {
            "user_id": session['user_id'],
            "email": session['email'],
            "role": session['role'],
            "avatar": avatar_url, # Biến này giờ đã an toàn
            "name": user_name
        }
    }), 200