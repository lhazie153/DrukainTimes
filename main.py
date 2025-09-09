import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from src.models import db, User, Post, Vote, MonthlyWinner, About
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.posts import posts_bp
from src.routes.admin import admin_bp
from src.routes.about import about_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'school_forum_secret_key_2024')

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(posts_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(about_bp, url_prefix='/api')

# Database configuration
# Database configuration - Use environment variable for production database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}" # Fallback for local dev
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # IMPORTANT: Remove or guard db.create_all() and initial data population
    # This should be done as a separate migration step, not on every app start.
    # For local development, you might keep it, but for Netlify, it's problematic.
    # with app.app_context():
    #     db.create_all()
    #     # ... (remove or guard initial user/post creation)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

    # Remove or guard this block for Netlify deployment
    # if __name__ == '__main__':
    #     app.run(host='0.0.0.0', port=5001, debug=True)


