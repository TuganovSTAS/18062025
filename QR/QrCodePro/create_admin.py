#!/usr/bin/env python3
"""
Script to create an admin account for the QR Platform
Run this once to set up your admin access
"""

from app import app, db
from models import Admin

def create_admin():
    """Create admin account"""
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(username='admin').first()
        if existing_admin:
            print("Admin account already exists!")
            return
        
        # Create new admin
        admin = Admin(
            username='admin',
            email='admin@qrplatform.com',
            is_super_admin=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Admin account created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Access: /admin/login")

if __name__ == '__main__':
    create_admin()