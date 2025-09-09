from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models import db, Post, Vote, MonthlyWinner
from datetime import datetime

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['GET'])
@login_required
def get_posts():
    """Get posts accessible to current user"""
    try:
        post_type = request.args.get('type')  # article, announcement, reminder, principal_note
        grade_level = request.args.get('grade_level')
        
        # Build query based on user permissions
        query = Post.query.filter_by(is_published=True)
        
        # Filter by post type if specified
        if post_type:
            query = query.filter_by(post_type=post_type)
        
        # Apply grade level filtering
        accessible_grades = current_user.get_accessible_grades()
        if grade_level and grade_level in accessible_grades:
            query = query.filter(Post.grade_level.in_([grade_level, 'all']))
        else:
            query = query.filter(Post.grade_level.in_(accessible_grades + ['all']))
        
        # Filter out expired announcements
        query = query.filter(
            db.or_(
                Post.expires_at.is_(None),
                Post.expires_at > datetime.utcnow()
            )
        )
        
        posts = query.order_by(Post.created_at.desc()).all()
        
        # Include vote information for articles
        posts_data = []
        for post in posts:
            post_dict = post.to_dict(include_votes=True)
            if post.can_be_voted_on():
                current_month = Vote.get_current_month()
                post_dict['user_has_voted'] = Vote.user_has_voted_this_month(
                    current_user.id, post.id, current_month
                )
            posts_data.append(post_dict)
        
        return jsonify({'posts': posts_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    """Get a specific post"""
    try:
        post = Post.query.get_or_404(post_id)
        
        # Check if user can access this post
        if not post.is_accessible_by_user(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        post_dict = post.to_dict(include_votes=True)
        if post.can_be_voted_on():
            current_month = Vote.get_current_month()
            post_dict['user_has_voted'] = Vote.user_has_voted_this_month(
                current_user.id, post.id, current_month
            )
        
        return jsonify({'post': post_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts', methods=['POST'])
@login_required
def create_post():
    """Create a new post"""
    try:
        # Check if user can create posts
        if not current_user.can_post():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'content', 'post_type', 'grade_level']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate post type
        valid_types = ['article', 'announcement', 'reminder']
        if current_user.role == 'admin' or current_user.role == 'language_teacher':
            valid_types.append('principal_note')
        
        if data['post_type'] not in valid_types:
            return jsonify({'error': 'Invalid post type'}), 400
        
        # Validate grade level
        valid_grades = ['junior', 'middle', 'senior', 'all']
        if data['grade_level'] not in valid_grades:
            return jsonify({'error': 'Invalid grade level'}), 400
        
        # Create new post
        post = Post(
            title=data['title'],
            content=data['content'],
            post_type=data['post_type'],
            grade_level=data['grade_level'],
            author_id=current_user.id
        )
        
        # Set expiration date for announcements if provided
        if data['post_type'] == 'announcement' and data.get('expires_at'):
            try:
                post.expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expiration date format'}), 400
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_on_post(post_id):
    """Vote on an article"""
    try:
        post = Post.query.get_or_404(post_id)
        
        # Check if post can be voted on
        if not post.can_be_voted_on():
            return jsonify({'error': 'This post cannot be voted on'}), 400
        
        # Check if user can access this post
        if not post.is_accessible_by_user(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        current_month = Vote.get_current_month()
        
        # Check if user has already voted this month
        if Vote.user_has_voted_this_month(current_user.id, post_id, current_month):
            return jsonify({'error': 'You have already voted on this article this month'}), 400
        
        # Create vote
        vote = Vote(
            user_id=current_user.id,
            post_id=post_id,
            vote_month=current_month
        )
        
        db.session.add(vote)
        db.session.commit()
        
        return jsonify({
            'message': 'Vote recorded successfully',
            'vote_count': post.get_vote_count(current_month)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/winners', methods=['GET'])
@login_required
def get_monthly_winners():
    """Get monthly winners"""
    try:
        month = request.args.get('month')  # Format: YYYY-MM
        grade_level = request.args.get('grade_level')
        
        if not month:
            month = Vote.get_current_month()
        
        # Filter by user's accessible grade levels
        accessible_grades = current_user.get_accessible_grades()
        if grade_level and grade_level not in accessible_grades:
            return jsonify({'error': 'Access denied to this grade level'}), 403
        
        if grade_level:
            winners = MonthlyWinner.get_winners_for_month(month, grade_level)
        else:
            all_winners = MonthlyWinner.get_winners_for_month(month)
            winners = [w for w in all_winners if w.grade_level in accessible_grades]
        
        winners_data = [winner.to_dict() for winner in winners]
        
        return jsonify({
            'winners': winners_data,
            'month': month
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/top-articles', methods=['GET'])
@login_required
def get_top_articles():
    """Get top voted articles for current month"""
    try:
        grade_level = request.args.get('grade_level')
        current_month = Vote.get_current_month()
        
        # Filter by user's accessible grade levels
        accessible_grades = current_user.get_accessible_grades()
        if grade_level and grade_level not in accessible_grades:
            return jsonify({'error': 'Access denied to this grade level'}), 403
        
        if grade_level:
            top_articles = Vote.get_monthly_vote_counts(current_month, grade_level)
        else:
            all_articles = Vote.get_monthly_vote_counts(current_month)
            top_articles = [a for a in all_articles if a.grade_level in accessible_grades]
        
        articles_data = []
        for article in top_articles[:10]:  # Top 10
            post = Post.query.get(article.id)
            if post:
                post_dict = post.to_dict()
                post_dict['vote_count'] = article.vote_count
                post_dict['user_has_voted'] = Vote.user_has_voted_this_month(
                    current_user.id, post.id, current_month
                )
                articles_data.append(post_dict)
        
        return jsonify({
            'top_articles': articles_data,
            'month': current_month
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

