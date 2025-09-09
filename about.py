from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., 'contact', 'history', 'mission'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # For ordering sections

    def __repr__(self):
        return f'<About {self.section_name}>'

    def to_dict(self):
        from .user import User
        creator = User.query.get(self.created_by)
        updater = User.query.get(self.updated_by)
        
        return {
            'id': self.id,
            'section_name': self.section_name,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'creator_name': f"{creator.first_name} {creator.last_name}" if creator else None,
            'updater_name': f"{updater.first_name} {updater.last_name}" if updater else None
        }

    @staticmethod
    def get_active_sections():
        """Get all active about sections ordered by display_order"""
        return About.query.filter_by(is_active=True).order_by(About.display_order.asc()).all()

    @staticmethod
    def get_section_by_name(section_name):
        """Get a specific section by name"""
        return About.query.filter_by(section_name=section_name, is_active=True).first()

    @staticmethod
    def create_default_sections(admin_user_id):
        """Create default about sections"""
        default_sections = [
            {
                'section_name': 'contact',
                'title': 'Contact Information',
                'content': '''
**Phone:** +975 17111111

**Email:** neanderthals.banana@gmail.com

**Address:** Druk School Campus
Thimphu, Bhutan

**Office Hours:**
Monday - Friday: 8:00 AM - 5:00 PM
Saturday: 9:00 AM - 1:00 PM
Sunday: Closed

**Emergency Contact:** +975 17111111
                ''',
                'display_order': 1
            },
            {
                'section_name': 'about_school',
                'title': 'About Druk School',
                'content': '''
Druk School is a premier educational institution committed to providing quality education and fostering holistic development of our students. 

**Our Mission:**
To nurture young minds and prepare them for the challenges of tomorrow while preserving our cultural heritage and values.

**Our Vision:**
To be a leading educational institution that produces confident, capable, and compassionate global citizens.

**Established:** 1985

**Student Population:** Over 1,200 students from Junior to Senior levels

**Faculty:** Highly qualified and experienced teachers dedicated to excellence in education.
                ''',
                'display_order': 2
            },
            {
                'section_name': 'facilities',
                'title': 'School Facilities',
                'content': '''
**Academic Facilities:**
- Modern classrooms with smart boards
- Well-equipped science laboratories
- Computer lab with latest technology
- Comprehensive library with digital resources

**Sports & Recreation:**
- Multi-purpose sports ground
- Basketball court
- Indoor games facility
- Gymnasium

**Other Facilities:**
- School cafeteria
- Medical room with qualified nurse
- Transportation service
- Hostel accommodation for outstation students

**Special Programs:**
- Cultural preservation activities
- Environmental conservation projects
- Community service initiatives
- International exchange programs
                ''',
                'display_order': 3
            },
            {
                'section_name': 'admissions',
                'title': 'Admissions Information',
                'content': '''
**Admission Process:**
1. Application form submission
2. Entrance examination (for certain grades)
3. Interview with parents and student
4. Document verification
5. Fee payment and enrollment

**Required Documents:**
- Birth certificate
- Previous academic records
- Medical certificate
- Passport-size photographs
- Parent/Guardian identification

**Admission Periods:**
- **Junior Level:** Applications open in January
- **Middle Level:** Applications open in February  
- **Senior Level:** Applications open in March

**For more information:**
Contact our admissions office at +975 17111111 or email neanderthals.banana@gmail.com

**Scholarship Programs:**
Merit-based scholarships available for outstanding students. Need-based financial assistance also provided.
                ''',
                'display_order': 4
            }
        ]
        
        for section_data in default_sections:
            existing = About.query.filter_by(section_name=section_data['section_name']).first()
            if not existing:
                section = About(
                    section_name=section_data['section_name'],
                    title=section_data['title'],
                    content=section_data['content'],
                    created_by=admin_user_id,
                    updated_by=admin_user_id,
                    display_order=section_data['display_order']
                )
                db.session.add(section)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

