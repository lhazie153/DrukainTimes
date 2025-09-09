from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, language_teacher, teacher, student, parent
    grade_level = db.Column(db.String(10), nullable=False)  # junior, middle, senior
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def can_post(self):
        """Check if user can create posts"""
        return self.role in ['admin', 'language_teacher']

    def can_moderate(self):
        """Check if user can moderate content"""
        return self.role == 'admin'

    def can_vote(self):
        """Check if user can vote on articles"""
        return self.is_active

    def get_accessible_grades(self):
        """Get list of grade levels user can access"""
        if self.role == 'admin':
            return ['junior', 'middle', 'senior']
        else:
            return [self.grade_level]

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'grade_level': self.grade_level,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

