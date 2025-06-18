from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    prefix = db.Column(db.String(6), unique=True, nullable=False)
    document_path = db.Column(db.String(500))  # Path to uploaded document
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with products
    products = db.relationship('Product', backref='company', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def generate_unique_prefix():
        """Generate a unique 6-digit company prefix"""
        while True:
            prefix = ''.join(random.choices('0123456789', k=6))
            if not Company.query.filter_by(prefix=prefix).first():
                return prefix
    
    def to_dict(self):
        """Convert company to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'prefix': self.prefix,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    product_hash = db.Column(db.String(64), unique=True, nullable=False)
    qr_code_path = db.Column(db.String(500))  # Path to QR code image
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'description': self.description,
            'image_url': self.image_url,
            'product_hash': self.product_hash,
            'qr_code_path': self.qr_code_path,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert admin to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
