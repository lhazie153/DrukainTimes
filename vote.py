from src.models.user import db
from datetime import datetime

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    vote_month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one vote per user per post per month
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', 'vote_month', name='unique_user_post_month_vote'),)

    @staticmethod
    def get_current_month():
        """Get current month in YYYY-MM format"""
        return datetime.utcnow().strftime('%Y-%m')

    @staticmethod
    def user_has_voted_this_month(user_id, post_id, month=None):
        """Check if user has already voted for this post this month"""
        if month is None:
            month = Vote.get_current_month()
        
        return Vote.query.filter_by(
            user_id=user_id,
            post_id=post_id,
            vote_month=month
        ).first() is not None

    @staticmethod
    def get_monthly_vote_counts(month, grade_level=None):
        """Get vote counts for all posts in a specific month and grade level"""
        from src.models.post import Post
        
        query = db.session.query(
            Post.id,
            Post.title,
            Post.grade_level,
            db.func.count(Vote.id).label('vote_count')
        ).join(Vote, Post.id == Vote.post_id).filter(
            Vote.vote_month == month,
            Post.post_type == 'article',
            Post.is_published == True
        )
        
        if grade_level:
            query = query.filter(Post.grade_level == grade_level)
        
        return query.group_by(Post.id).order_by(db.desc('vote_count')).all()

    def __repr__(self):
        return f'<Vote user_id={self.user_id} post_id={self.post_id} month={self.vote_month}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'vote_month': self.vote_month,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

