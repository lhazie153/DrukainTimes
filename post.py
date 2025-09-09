from src.models.user import db
from datetime import datetime

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(20), nullable=False)  # article, announcement, reminder, principal_note
    grade_level = db.Column(db.String(10), nullable=False)  # junior, middle, senior, all
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # For announcements with expiration
    
    # Relationships
    votes = db.relationship('Vote', backref='post', lazy=True, cascade='all, delete-orphan')
    monthly_wins = db.relationship('MonthlyWinner', backref='post', lazy=True)

    def get_vote_count(self, month=None):
        """Get vote count for this post, optionally for a specific month"""
        if month:
            return Vote.query.filter_by(post_id=self.id, vote_month=month).count()
        return len(self.votes)

    def can_be_voted_on(self):
        """Check if this post can receive votes (only articles)"""
        return self.post_type == 'article' and self.is_published

    def is_expired(self):
        """Check if this post has expired (for announcements)"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def is_accessible_by_user(self, user):
        """Check if user can access this post based on grade level"""
        if user.role == 'admin':
            return True
        if self.grade_level == 'all':
            return True
        return self.grade_level == user.grade_level

    def __repr__(self):
        return f'<Post {self.title}>'

    def to_dict(self, include_votes=False):
        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'post_type': self.post_type,
            'grade_level': self.grade_level,
            'author_id': self.author_id,
            'author_name': f"{self.author.first_name} {self.author.last_name}" if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_published': self.is_published,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }
        
        if include_votes and self.can_be_voted_on():
            current_month = datetime.utcnow().strftime('%Y-%m')
            result['vote_count'] = self.get_vote_count(current_month)
            result['total_votes'] = self.get_vote_count()
        
        return result

