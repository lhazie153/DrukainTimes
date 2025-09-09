from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models import db, User, Post, Vote, MonthlyWinner
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_moderate():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        users_data = [user.to_dict() for user in users]
        return jsonify({'users': users_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user information (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'role' in data:
            valid_roles = ['admin', 'language_teacher', 'teacher', 'student', 'parent']
            if data['role'] in valid_roles:
                user.role = data['role']
        
        if 'grade_level' in data:
            valid_grades = ['junior', 'middle', 'senior']
            if data['grade_level'] in valid_grades:
                user.grade_level = data['grade_level']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/posts/all', methods=['GET'])
@login_required
@admin_required
def get_all_posts():
    """Get all posts including unpublished (admin only)"""
    try:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        posts_data = [post.to_dict(include_votes=True) for post in posts]
        return jsonify({'posts': posts_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
@admin_required
def update_post(post_id):
    """Update post (admin only)"""
    try:
        post = Post.query.get_or_404(post_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            post.title = data['title']
        
        if 'content' in data:
            post.content = data['content']
        
        if 'is_published' in data:
            post.is_published = bool(data['is_published'])
        
        if 'grade_level' in data:
            valid_grades = ['junior', 'middle', 'senior', 'all']
            if data['grade_level'] in valid_grades:
                post.grade_level = data['grade_level']
        
        if 'expires_at' in data:
            if data['expires_at']:
                try:
                    post.expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid expiration date format'}), 400
            else:
                post.expires_at = None
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_post(post_id):
    """Delete post (admin only)"""
    try:
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/calculate-winners', methods=['POST'])
@login_required
@admin_required
def calculate_monthly_winners():
    """Calculate monthly winners (admin only)"""
    try:
        data = request.get_json()
        month = data.get('month', Vote.get_current_month())
        
        winners = MonthlyWinner.calculate_monthly_winners(month)
        winners_data = [winner.to_dict() for winner in winners]
        
        return jsonify({
            'message': f'Monthly winners calculated for {month}',
            'winners': winners_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    """Get system statistics (admin only)"""
    try:
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'total_posts': Post.query.count(),
            'published_posts': Post.query.filter_by(is_published=True).count(),
            'total_votes': Vote.query.count(),
            'users_by_role': {},
            'users_by_grade': {},
            'posts_by_type': {},
            'posts_by_grade': {}
        }
        
        # Users by role
        for role in ['admin', 'language_teacher', 'teacher', 'student', 'parent']:
            stats['users_by_role'][role] = User.query.filter_by(role=role).count()
        
        # Users by grade
        for grade in ['junior', 'middle', 'senior']:
            stats['users_by_grade'][grade] = User.query.filter_by(grade_level=grade).count()
        
        # Posts by type
        for post_type in ['article', 'announcement', 'reminder', 'principal_note']:
            stats['posts_by_type'][post_type] = Post.query.filter_by(post_type=post_type).count()
        
        # Posts by grade
        for grade in ['junior', 'middle', 'senior', 'all']:
            stats['posts_by_grade'][grade] = Post.query.filter_by(grade_level=grade).count()
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

