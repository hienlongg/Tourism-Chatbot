"""
Posts routes for travel guides and tips.
Handles CRUD operations for user-generated content.
"""

from flask import Blueprint, request, session, jsonify
from backend.models.post import PostModel, LocationField, AuthorField
from backend.middlewares.decorators import login_required
from backend.utils.post_validator import validate_post_data
from datetime import datetime, timezone
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

# Create posts blueprint
posts_bp = Blueprint('posts', __name__, url_prefix='/api/posts')


@posts_bp.route('/create', methods=['POST'])
@login_required
def create_post():
    """
    Create a new travel guide/tips post.
    
    Request Body:
        type: str - Post type (guide or itinerary)
        title: str - Post title
        description: str - Short description
        content: str - Main content
        location: dict - Location data {name, lat, lng}
        images: list - Image URLs
        tags: list - Tags
        isPublished: bool - Publishing status
        
    Returns:
        201: Post created successfully
        400: Validation error
    """
    try:
        data = request.get_json()
        
        # Get post type (default to guide)
        post_type = data.get('type', 'guide')
        
        # Validate post data
        is_valid, error = validate_post_data(data, post_type)
        if not is_valid:
            return jsonify({"message": error}), 400
        
        # Create location embedded document
        location_data = data.get('location')
        location = LocationField(
            name=location_data['name'],
            lat=location_data.get('lat'),
            lng=location_data.get('lng')
        )
        
        # Auto-fetch image if not provided
        images = data.get('images', [])
        if not images and location_data.get('name'):
            # Try to fetch image from Google Custom Search
            from backend.utils.image_resolver import fetch_image_from_google
            
            logger.info(f"Auto-fetching image for location: {location_data['name']}")
            google_image = fetch_image_from_google(location_data['name'])
            
            if google_image:
                images = [google_image]
                logger.info(f"Found image: {google_image}")
            else:
                logger.warning(f"No image found for: {location_data['name']}")
        
        # Create author embedded document
        author = AuthorField(
            user_id=ObjectId(session['user_id']),
            email=session['email']
        )
        
        # Create post
        post = PostModel(
            type=post_type,
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            content=data['content'].strip(),
            location=location,
            images=images,  # ← Now includes auto-fetched image!
            tags=[tag.strip().lower() for tag in data.get('tags', [])],
            author=author,
            is_published=data.get('isPublished', True)
        )
        
        # Save to database
        post.save()
        
        logger.info(f"Post created: {post.post_id} by user {session['user_id']}")
        
        return jsonify({
            "message": "Post created successfully",
            "post": post.to_dict(include_author_email=True)
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        return jsonify({"message": "Failed to create post", "error": str(e)}), 500


@posts_bp.route('', methods=['GET'])
def list_posts():
    """
    List posts with filters and pagination.
    
    Query Parameters:
        type: str - Filter by type (guide/itinerary)
        location: str - Filter by location name (partial match)
        tags: str - Comma-separated tags
        author: str - Filter by author user ID
        page: int - Page number (default: 1)
        limit: int - Items per page (default: 10, max: 50)
        sort: str - Sort by (newest/popular/trending)
        
    Returns:
        200: List of posts with pagination metadata
    """
    try:
        # Get query parameters
        post_type = request.args.get('type')
        location = request.args.get('location')
        tags = request.args.get('tags')
        author_id = request.args.get('author')
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)
        sort_by = request.args.get('sort', 'newest')
        
        # Build query
        query = {'is_deleted': False, 'is_published': True}
        
        if post_type:
            query['type'] = post_type
        
        if location:
            query['location__name__icontains'] = location
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(',')]
            query['tags__in'] = tag_list
        
        if author_id:
            query['author__user_id'] = ObjectId(author_id)
        
        # Build sort
        if sort_by == 'popular':
            sort = '-likes'  # Most likes first
        elif sort_by == 'trending':
            sort = '-views'  # Most views first
        else:  # newest
            sort = '-created_at'
        
        # Execute query with pagination
        skip = (page - 1) * limit
        posts = PostModel.objects(**query).order_by(sort).skip(skip).limit(limit)
        total = PostModel.objects(**query).count()
        
        # Convert to dict with author email included
        posts_data = [post.to_dict(include_author_email=True) for post in posts]
        
        return jsonify({
            "posts": posts_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing posts: {str(e)}")
        return jsonify({"message": "Failed to list posts", "error": str(e)}), 500


@posts_bp.route('/<post_id>', methods=['GET'])
def get_post(post_id):
    """
    Get a single post by ID and increment view count.
    
    Args:
        post_id: Post ID
        
    Returns:
        200: Post data
        404: Post not found
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Find post
        post = PostModel.objects(post_id=ObjectId(post_id), is_deleted=False).first()
        
        if not post:
            return jsonify({"message": "Post not found"}), 404
        
        # Increment views
        post.increment_views()
        
        # Check if current user is the author
        is_author = False
        if 'user_id' in session:
            is_author = str(post.author.user_id) == session['user_id']
        
        return jsonify({
            "post": post.to_dict(include_author_email=is_author)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting post: {str(e)}")
        return jsonify({"message": "Failed to get post", "error": str(e)}), 500


@posts_bp.route('/<post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    """
    Update a post. Only the author can update.
    
    Args:
        post_id: Post ID
        
    Request Body:
        Same as create_post (all fields optional)
        
    Returns:
        200: Post updated successfully
        403: Not authorized
        404: Post not found
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Find post
        post = PostModel.objects(post_id=ObjectId(post_id), is_deleted=False).first()
        
        if not post:
            return jsonify({"message": "Post not found"}), 404
        
        # Check authorization
        if str(post.author.user_id) != session['user_id']:
            return jsonify({"message": "Not authorized to update this post"}), 403
        
        # Get update data
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            post.title = data['title'].strip()
        
        if 'description' in data:
            post.description = data['description'].strip()
        
        if 'content' in data:
            post.content = data['content'].strip()
        
        if 'location' in data:
            location_data = data['location']
            post.location = LocationField(
                name=location_data['name'],
                lat=location_data.get('lat'),
                lng=location_data.get('lng')
            )
        
        if 'images' in data:
            post.images = data['images']
        
        if 'tags' in data:
            post.tags = [tag.strip().lower() for tag in data['tags']]
        
        if 'isPublished' in data:
            post.is_published = data['isPublished']
        
        # Update timestamp
        post.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        post.save()
        
        logger.info(f"Post updated: {post_id} by user {session['user_id']}")
        
        return jsonify({
            "message": "Post updated successfully",
            "post": post.to_dict(include_author_email=True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating post: {str(e)}")
        return jsonify({"message": "Failed to update post", "error": str(e)}), 500


@posts_bp.route('/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """
    Delete a post (soft delete). Only the author can delete.
    
    Args:
        post_id: Post ID
        
    Returns:
        200: Post deleted successfully
        403: Not authorized
        404: Post not found
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Find post
        post = PostModel.objects(post_id=ObjectId(post_id), is_deleted=False).first()
        
        if not post:
            return jsonify({"message": "Post not found"}), 404
        
        # Check authorization
        if str(post.author.user_id) != session['user_id']:
            return jsonify({"message": "Not authorized to delete this post"}), 403
        
        # Soft delete
        post.is_deleted = True
        post.updated_at = datetime.now(timezone.utc)
        post.save()
        
        logger.info(f"Post deleted: {post_id} by user {session['user_id']}")
        
        return jsonify({"message": "Post deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        return jsonify({"message": "Failed to delete post", "error": str(e)}), 500


@posts_bp.route('/<post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    """
    Toggle like on a post.
    
    Args:
        post_id: Post ID
        
    Returns:
        200: Like toggled successfully
        404: Post not found
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Find post
        post = PostModel.objects(post_id=ObjectId(post_id), is_deleted=False).first()
        
        if not post:
            return jsonify({"message": "Post not found"}), 404
        
        # Toggle like
        user_id = session['user_id']
        new_like_count = post.toggle_like(user_id)
        
        is_liked = user_id in post.likes
        
        logger.info(f"Post {post_id} {'liked' if is_liked else 'unliked'} by user {user_id}")
        
        return jsonify({
            "message": "Like toggled successfully",
            "likeCount": new_like_count,
            "isLiked": is_liked
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling like: {str(e)}")
        return jsonify({"message": "Failed to toggle like", "error": str(e)}), 500


@posts_bp.route('/user/<user_id>', methods=['GET'])
def get_user_posts(user_id):
    """
    Get all posts by a specific user.
    
    Args:
        user_id: User ID
        
    Query Parameters:
        Same as list_posts
        
    Returns:
        200: List of user's posts
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            return jsonify({"message": "Invalid user ID"}), 400
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Build query
        query = {
            'author__user_id': ObjectId(user_id),
            'is_deleted': False,
            'is_published': True
        }
        
        # Execute query with pagination
        skip = (page - 1) * limit
        posts = PostModel.objects(**query).order_by('-created_at').skip(skip).limit(limit)
        total = PostModel.objects(**query).count()
        
        # Convert to dict
        posts_data = [post.to_dict() for post in posts]
        
        return jsonify({
            "posts": posts_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user posts: {str(e)}")
        return jsonify({"message": "Failed to get user posts", "error": str(e)}), 500


@posts_bp.route('/<post_id>/save', methods=['POST'])
@login_required
def toggle_save(post_id):
    """
    Save or unsave a post (bookmark).
    
    Args:
        post_id: Post ID
        
    Returns:
        200: Save toggled successfully
        404: Post not found
    """
    try:
        from flask import current_app
        
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Find post
        post = PostModel.objects(post_id=ObjectId(post_id), is_deleted=False).first()
        
        if not post:
            return jsonify({"message": "Post not found"}), 404
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        user_id = session['user_id']
        
        # Check if post is already saved
        saved_post = db.saved_posts.find_one({
            "userId": user_id,
            "postId": str(post.post_id)
        })
        
        if saved_post:
            # Unsave - remove from saved_posts
            db.saved_posts.delete_one({
                "userId": user_id,
                "postId": str(post.post_id)
            })
            is_saved = False
            message = "Post removed from saved"
        else:
            # Save - add to saved_posts
            db.saved_posts.insert_one({
                "userId": user_id,
                "postId": str(post.post_id),
                "savedAt": datetime.now(timezone.utc)
            })
            is_saved = True
            message = "Post saved successfully"
        
        logger.info(f"Post {post_id} {'saved' if is_saved else 'unsaved'} by user {user_id}")
        
        return jsonify({
            "message": message,
            "isSaved": is_saved
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling save: {str(e)}")
        return jsonify({"message": "Failed to toggle save", "error": str(e)}), 500


@posts_bp.route('/<post_id>/saved-status', methods=['GET'])
@login_required
def check_saved_status(post_id):
    """
    Check if a post is saved by current user.
    
    Args:
        post_id: Post ID
        
    Returns:
        200: Saved status
    """
    try:
        from flask import current_app
        
        # Validate ObjectId
        if not ObjectId.is_valid(post_id):
            return jsonify({"message": "Invalid post ID"}), 400
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        user_id = session['user_id']
        
        # Check if post is saved
        saved_post = db.saved_posts.find_one({
            "userId": user_id,
            "postId": post_id
        })
        
        return jsonify({
            "isSaved": saved_post is not None
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking saved status: {str(e)}")
        return jsonify({"message": "Failed to check saved status", "error": str(e)}), 500


@posts_bp.route('/saved', methods=['GET'])
@login_required
def get_saved_posts():
    """
    Get user's saved posts.
    
    Query Parameters:
        page: int - Page number (default: 1)
        limit: int - Items per page (default: 10, max: 50)
        
    Returns:
        200: List of saved posts with pagination
    """
    try:
        from flask import current_app
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        user_id = session['user_id']
        
        # Get saved post IDs with pagination
        skip = (page - 1) * limit
        saved_posts = list(db.saved_posts.find(
            {"userId": user_id}
        ).sort("savedAt", -1).skip(skip).limit(limit))
        
        total = db.saved_posts.count_documents({"userId": user_id})
        
        # Get post IDs
        post_ids = [ObjectId(sp["postId"]) for sp in saved_posts]
        
        if not post_ids:
            return jsonify({
                "posts": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "totalPages": 0
                }
            }), 200
        
        # Fetch FULL posts from PostModel (not cached data)
        # This ensures we always get latest data with author email
        posts = PostModel.objects(post_id__in=post_ids, is_deleted=False)
        
        # Create a map of post_id to savedAt
        saved_at_map = {sp["postId"]: sp["savedAt"] for sp in saved_posts}
        
        # Convert to dict with author email included
        posts_data = []
        for post in posts:
            post_dict = post.to_dict(include_author_email=True)  # ← Include email!
            post_dict["savedAt"] = saved_at_map.get(str(post.post_id)).isoformat() if saved_at_map.get(str(post.post_id)) else None
            post_dict["isSaved"] = True  # All posts in this list are saved
            posts_data.append(post_dict)
        
        # Sort by savedAt (newest first)
        posts_data.sort(key=lambda x: x.get("savedAt", ""), reverse=True)
        
        return jsonify({
            "posts": posts_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting saved posts: {str(e)}")
        return jsonify({"message": "Failed to get saved posts", "error": str(e)}), 500
