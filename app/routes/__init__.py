# app/routes/__init__.py

from .auth import auth_bp
from .core import core_bp
from .citizen import citizen_bp
from .api import api_bp
from .admin import admin_bp

#blueprint export here

__all__ = [
    'auth_bp',
    'core_bp',
    'citizen_bp',
    'api_bp',
    'admin_bp',
    'spatial_bp'
]