"""
Upload routes for file handling.
Provides REST API endpoints for image uploads.
"""

from flask import Blueprint, request, jsonify, current_app
from backend.middlewares.decorators import login_required
import logging
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../../uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.
    
    Args:
        filename: File name to check
    
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_upload_directory():
    """Create upload directory if it doesn't exist."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"Created upload directory: {UPLOAD_FOLDER}")


@upload_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for upload service."""
    return jsonify({
        "status": "healthy",
        "upload_folder": UPLOAD_FOLDER,
        "max_file_size": MAX_FILE_SIZE
    }), 200


@upload_bp.route('/image', methods=['POST'])
@login_required
def upload_image():
    """
    Upload an image file.
    
    Request:
        - Method: POST
        - Content-Type: multipart/form-data
        - Field name: 'file' (required)
    
    Response:
        {
            "success": true,
            "url": "/uploads/image_filename.jpg",
            "filename": "image_filename.jpg",
            "message": "Image uploaded successfully"
        }
    
    Error Response:
        {
            "success": false,
            "error": "Error message"
        }
    """
    try:
        # Check if request has file part
        if 'file' not in request.files:
            logger.warning("Upload request missing 'file' field")
            return jsonify({
                "success": False,
                "error": "No file provided. Please include a 'file' field in your request."
            }), 400
        
        file = request.files['file']
        
        # Check if file was actually selected
        if file.filename == '':
            logger.warning("Upload request with empty filename")
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.warning(f"Upload attempt with disallowed file type: {file.filename}")
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"Upload attempt with oversized file: {file_size} bytes")
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            }), 413
        
        if file_size == 0:
            logger.warning("Upload attempt with empty file")
            return jsonify({
                "success": False,
                "error": "File is empty"
            }), 400
        
        # Create upload directory if needed
        create_upload_directory()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        filename = f"image_{timestamp}_{os.urandom(4).hex()}.{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        logger.info(f"Image uploaded successfully: {filename}")
        
        # Return relative URL for client
        url = f"/uploads/{filename}"
        
        return jsonify({
            "success": True,
            "url": url,
            "filename": filename,
            "message": "Image uploaded successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error uploading image: {str(e)}"
        }), 500


@upload_bp.route('/image/<filename>', methods=['GET'])
def serve_image(filename: str):
    """
    Serve an uploaded image via HTTP.
    
    Args:
        filename: Name of the image file to serve
    
    Response:
        Image file with appropriate Content-Type header
        or 404 if file not found
    """
    try:
        from flask import send_from_directory, abort
        
        # Validate filename (prevent directory traversal attacks)
        if '..' in filename or '/' in filename:
            logger.warning(f"Invalid filename attempted: {filename}")
            abort(400)
        
        # Check if file exists
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Requested image not found: {filename}")
            abort(404)
        
        # Check if it's actually a file (not directory)
        if not os.path.isfile(filepath):
            logger.warning(f"Requested path is not a file: {filename}")
            abort(404)
        
        logger.info(f"✅ Serving image: {filename}")
        return send_from_directory(UPLOAD_FOLDER, filename)
        
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        abort(500)


@upload_bp.route('/post-image', methods=['POST'])
@login_required
def upload_post_image():
    """
    Upload multiple images for posts (local storage).
    Supports up to 5 images per request.
    
    Request:
        - Method: POST
        - Content-Type: multipart/form-data
        - Field name: 'images' (can be multiple files)
    
    Response:
        {
            "success": true,
            "urls": ["/uploads/image1.jpg", "/uploads/image2.jpg"],
            "message": "2 image(s) uploaded successfully"
        }
    """
    try:
        # Check if request has file part
        if 'images' not in request.files:
            logger.warning("Upload request missing 'images' field")
            return jsonify({
                "success": False,
                "error": "No images provided. Please include 'images' field in your request."
            }), 400
        
        files = request.files.getlist('images')
        
        if not files or len(files) == 0:
            return jsonify({
                "success": False,
                "error": "No images selected"
            }), 400
        
        # Limit to 5 images per request
        if len(files) > 5:
            return jsonify({
                "success": False,
                "error": "Maximum 5 images allowed per request"
            }), 400
        
        # Create upload directory if needed
        create_upload_directory()
        
        uploaded_urls = []
        
        for file in files:
            # Check if file was actually selected
            if file.filename == '':
                continue
            
            # Check file extension
            if not allowed_file(file.filename):
                logger.warning(f"Upload attempt with disallowed file type: {file.filename}")
                return jsonify({
                    "success": False,
                    "error": f"File type not allowed for {file.filename}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                }), 400
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"Upload attempt with oversized file: {file_size} bytes")
                return jsonify({
                    "success": False,
                    "error": f"File {file.filename} too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
                }), 413
            
            if file_size == 0:
                continue
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
            filename = f"post_{timestamp}_{os.urandom(4).hex()}.{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save file
            file.save(filepath)
            logger.info(f"Image uploaded: {filename}")
            
            # Add URL to list
            uploaded_urls.append(f"/uploads/{filename}")
        
        if not uploaded_urls:
            return jsonify({
                "success": False,
                "error": "No valid images were uploaded"
            }), 400
        
        return jsonify({
            "success": True,
            "urls": uploaded_urls,
            "message": f"{len(uploaded_urls)} image(s) uploaded successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading images: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error uploading images: {str(e)}"
        }), 500
