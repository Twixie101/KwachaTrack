# config.py
import os

class Config:
    """Base structural configuration parameters."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_highly_secure_crypto_string_2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///kwachatrack.db'
    )

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Enforce production configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    @classmethod
    def init_app(cls, app):
        # Handle production-level logger initializations or proxy handshakes here
        pass

config_matrix = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}