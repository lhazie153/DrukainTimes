from src.models.user import db
from datetime import datetime

class MonthlyWinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    grade_level = db.Column(db.String(10), nullable=False)  # junior, middle, senior
    vote_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one winner per grade level per month
    __table_args__ = (db.UniqueConstraint('month', 'grade_level', name='unique_month_grade_winner'),)

    @staticmethod
    def calculate_monthly_winners(month):
        """Calculate and store winners for a specific month"""
        from src.models.vote import Vote
        from src.models.post import Post
        
        grade_levels = ['junior', 'middle', 'senior']
        winners = []
        
        for grade_level in grade_levels:
            # Get the top voted article for this grade level and month
            top_article = db.session.query(
                Post.id,
                db.func.count(Vote.id).label('vote_count')
            ).join(Vote, Post.id == Vote.post_id).filter(
                Vote.vote_month == month,
                Post.post_type == 'article',
                Post.is_published == True,
                Post.grade_level == grade_level
            ).group_by(Post.id).order_by(db.desc('vote_count')).first()
            
            if top_article and top_article.vote_count > 0:
                # Check if winner already exists for this month and grade
                existing_winner = MonthlyWinner.query.filter_by(
                    month=month,
                    grade_level=grade_level
                ).first()
                
                if not existing_winner:
                    winner = MonthlyWinner(
                        post_id=top_article.id,
                        month=month,
                        grade_level=grade_level,
                        vote_count=top_article.vote_count
                    )
                    db.session.add(winner)
                    winners.append(winner)
        
        if winners:
            db.session.commit()
        
        return winners

    @staticmethod
    def get_winners_for_month(month, grade_level=None):
        """Get winners for a specific month, optionally filtered by grade level"""
        query = MonthlyWinner.query.filter_by(month=month)
        
        if grade_level:
            query = query.filter_by(grade_level=grade_level)
        
        return query.all()

    @staticmethod
    def get_recent_winners(limit=5, grade_level=None):
        """Get recent winners, optionally filtered by grade level"""
        query = MonthlyWinner.query.order_by(MonthlyWinner.month.desc())
        
        if grade_level:
            query = query.filter_by(grade_level=grade_level)
        
        return query.limit(limit).all()

    def __repr__(self):
        return f'<MonthlyWinner post_id={self.post_id} month={self.month} grade={self.grade_level}>'

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'post_title': self.post.title if self.post else None,
            'post_author': f"{self.post.author.first_name} {self.post.author.last_name}" if self.post and self.post.author else None,
            'month': self.month,
            'grade_level': self.grade_level,
            'vote_count': self.vote_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

