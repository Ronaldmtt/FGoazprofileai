"""
Script to initialize production database with clean data.
Run this once after first deployment to set up admin user.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Session, Item, Response, ProficiencySnapshot, Audit

def init_production_db():
    """Initialize production database with clean data."""
    app = create_app()
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        print("Production database initialized successfully!")
        print("No users created - users will be created via login flow.")
        print("\nAdmin access: /admin/login")
        print("Admin credentials are set via ADMIN_USERNAME and ADMIN_PASSWORD secrets.")

if __name__ == '__main__':
    init_production_db()
