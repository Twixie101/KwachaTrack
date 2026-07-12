# app/__init__.py
import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from app.models import db, User
from app.extensions import limiter 
from datetime import timedelta # <--- IMPORT THIS

# Instantiate LoginManager
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kwachatrack_secure_key_2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///kwachatrack.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # Bind extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Import blueprints inside the function to prevent circular errors
    from app.routes.core import core_bp
    from app.routes.auth import auth_bp
    from app.routes.citizen import citizen_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.api import api_bp
    from app.routes.map import spatial_bp

    
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp, url_prefix='/system-internal-control-824')
    app.register_blueprint(spatial_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))