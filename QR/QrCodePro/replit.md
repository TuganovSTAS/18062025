# QR Platform - B2B QR Code Generation System

## Overview

This is a Flask-based B2B QR code generation platform that allows companies to register, manage products, and generate branded QR codes. The system provides a complete workflow from company registration to product management with automatic QR code generation.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Database**: SQLAlchemy ORM with SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-JWT-Extended for token-based authentication
- **File Handling**: Werkzeug for secure file uploads
- **QR Code Generation**: qrcode library with PIL for image processing

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **Responsive Design**: Mobile-first approach

### Deployment Strategy
- **WSGI Server**: Gunicorn with auto-scaling deployment target
- **Environment**: Replit with Nix package management
- **Port Configuration**: 5000 with proxy fix for production

## Key Components

### 1. Company Management System
- **Registration**: Companies register with unique 6-digit prefixes
- **Authentication**: Password hashing with Werkzeug
- **Document Upload**: Business verification documents
- **Profile Management**: Company information and verification status

### 2. Product Management System
- **Product Creation**: Name, description, and image uploads
- **Hash Generation**: SHA256 hashes for unique product identification
- **QR Code Generation**: Automatic QR codes linking to product pages
- **File Storage**: Organized static file structure

### 3. QR Code System
- **URL Structure**: `/product/{company_prefix}/{product_hash}`
- **Dynamic Generation**: QR codes created on product addition
- **Storage**: Static files in `/static/qr_codes/`
- **Error Correction**: Level L for optimal scanning

### 4. Database Schema
```sql
Company Table:
- id (Primary Key)
- company_name, email (unique), phone_number
- password_hash (Werkzeug hashed)
- prefix (6-digit unique identifier)
- document_path, is_verified
- created_at timestamp

Product Table:
- id (Primary Key)
- company_id (Foreign Key to Company)
- product_name, description
- product_hash (SHA256 unique identifier)
- image_url, qr_code_path
- created_at timestamp
```

## Data Flow

### Company Registration Flow
1. Company submits registration form
2. System generates unique 6-digit prefix
3. Password is hashed using Werkzeug
4. Optional document upload with secure filename handling
5. Company record created in database
6. Automatic login session establishment

### Product Creation Flow
1. Authenticated company submits product form
2. SHA256 hash generated from product name + timestamp
3. Product image uploaded to `/static/uploads/`
4. QR code generated pointing to product page
5. QR code saved to `/static/qr_codes/`
6. Product record created with all metadata

### Product Access Flow
1. QR code scanned or URL accessed
2. System parses company prefix and product hash
3. Database lookup for product and company
4. Dynamic product page rendered with all details
5. Error handling for non-existent products

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM
- **Flask-JWT-Extended**: Authentication tokens
- **email-validator**: Email validation
- **gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL adapter
- **qrcode**: QR code generation
- **Pillow**: Image processing

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library
- **Custom CSS**: Hover effects and responsive design

### System Packages
- **PostgreSQL**: Production database
- **OpenSSL**: Security and encryption

## Deployment Strategy

### Development Environment
- SQLite database for local development
- Flask development server with debug mode
- Hot reloading for development workflow

### Production Environment
- Gunicorn WSGI server with bind to 0.0.0.0:5000
- PostgreSQL database via DATABASE_URL environment variable
- Connection pooling with ping and recycle settings
- ProxyFix middleware for proper headers

### File Management
- Upload size limit: 16MB maximum
- Organized static directories for uploads and QR codes
- Secure filename handling to prevent directory traversal
- Automatic directory creation on startup

### Security Features
- Password hashing with Werkzeug
- JWT token authentication
- File upload validation
- SQL injection prevention via SQLAlchemy ORM
- CSRF protection via Flask forms

## Changelog
- June 16, 2025. Initial setup
- June 16, 2025. Added admin system with company monitoring and statistics
- June 16, 2025. Added company deletion functionality with multi-step confirmation and file cleanup

## User Preferences

Preferred communication style: Simple, everyday language.