import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.utils import secure_filename
from app import app, db
from models import Company, Product, Admin
from utils import generate_product_hash, generate_qr_code, allowed_file, save_uploaded_file, create_qr_code_path

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Company registration"""
    if request.method == 'POST':
        try:
            # Get form data
            company_name = request.form.get('company_name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone_number = request.form.get('phone_number')
            
            # Validate required fields
            if not all([company_name, email, password, phone_number]):
                flash('All fields are required', 'error')
                return render_template('register.html')
            
            # Check if email already exists
            if Company.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return render_template('register.html')
            
            # Generate unique company prefix
            prefix = Company.generate_unique_prefix()
            
            # Create new company
            company = Company(
                company_name=company_name,
                email=email,
                phone_number=phone_number,
                prefix=prefix
            )
            company.set_password(password)
            
            # Handle document upload
            if 'document' in request.files:
                file = request.files['document']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        document_path = save_uploaded_file(file, current_app.config["UPLOAD_FOLDER"])
                        company.document_path = document_path
                        company.is_verified = True  # Mock verification - in real app, this would be manual
                    except Exception as e:
                        flash(f'Error uploading document: {str(e)}', 'error')
                        return render_template('register.html')
            
            # Save to database
            db.session.add(company)
            db.session.commit()
            
            flash(f'Registration successful! Your company prefix is: {prefix}', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Company login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        # Find company by email
        company = Company.query.filter_by(email=email).first()
        
        if company and company.check_password(password):
            # Create JWT token
            access_token = create_access_token(identity=company.id)
            
            # Store token in session for web interface
            from flask import session
            session['access_token'] = access_token
            session['company_id'] = company.id
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    from flask import session
    session.pop('access_token', None)
    session.pop('company_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Company dashboard"""
    from flask import session
    
    if 'company_id' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    try:
        company = Company.query.get(session['company_id'])
        if not company:
            flash('Company not found', 'error')
            return redirect(url_for('login'))
        
        # Get company's products
        products = Product.query.filter_by(company_id=company.id).order_by(Product.created_at.desc()).all()
        
        return render_template('dashboard.html', company=company, products=products)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """Add new product"""
    from flask import session
    
    if 'company_id' not in session:
        flash('Please login to add products', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            company_id = session['company_id']
            company = Company.query.get(company_id)
            
            if not company:
                flash('Company not found', 'error')
                return redirect(url_for('login'))
            
            # Get form data
            product_name = request.form.get('product_name')
            description = request.form.get('description', '')
            
            if not product_name:
                flash('Product name is required', 'error')
                return render_template('add_product.html')
            
            # Generate unique product hash
            product_hash = generate_product_hash(product_name)
            
            # Handle image upload
            image_url = None
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
                    try:
                        image_path = save_uploaded_file(file, current_app.config["UPLOAD_FOLDER"])
                        image_url = url_for('static', filename=f'uploads/{os.path.basename(image_path)}')
                    except Exception as e:
                        flash(f'Error uploading image: {str(e)}', 'warning')
            
            # Create new product
            product = Product(
                product_name=product_name,
                description=description,
                image_url=image_url,
                product_hash=product_hash,
                company_id=company_id
            )
            
            # Generate QR code
            qr_code_path = create_qr_code_path(company.prefix, product_hash)
            generate_qr_code(company.prefix, product_hash, qr_code_path)
            product.qr_code_path = qr_code_path
            
            # Save to database
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
            return render_template('add_product.html')
    
    return render_template('add_product.html')

@app.route('/product/<company_prefix>/<product_hash>')
def product_detail(company_prefix, product_hash):
    """Display product details"""
    try:
        # Find company by prefix
        company = Company.query.filter_by(prefix=company_prefix).first()
        if not company:
            flash('Company not found', 'error')
            return render_template('product_detail.html', error='Company not found')
        
        # Find product by hash
        product = Product.query.filter_by(product_hash=product_hash, company_id=company.id).first()
        if not product:
            flash('Product not found', 'error')
            return render_template('product_detail.html', error='Product not found')
        
        return render_template('product_detail.html', product=product, company=company)
        
    except Exception as e:
        return render_template('product_detail.html', error=f'Error loading product: {str(e)}')

@app.route('/generate_qr/<product_hash>')
def generate_qr_route(product_hash):
    """Generate and serve QR code image"""
    try:
        # Find product by hash
        product = Product.query.filter_by(product_hash=product_hash).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check if QR code file exists
        if product.qr_code_path and os.path.exists(product.qr_code_path):
            return send_file(product.qr_code_path, mimetype='image/png')
        
        # Generate QR code if it doesn't exist
        company = Company.query.get(product.company_id)
        qr_code_path = create_qr_code_path(company.prefix, product_hash)
        generate_qr_code(company.prefix, product_hash, qr_code_path)
        
        # Update product with QR code path
        product.qr_code_path = qr_code_path
        db.session.commit()
        
        return send_file(qr_code_path, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': f'Error generating QR code: {str(e)}'}), 500

# API Endpoints for programmatic access

@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for company registration"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['company_name', 'email', 'password', 'phone_number']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if email already exists
        if Company.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Generate unique company prefix
        prefix = Company.generate_unique_prefix()
        
        # Create new company
        company = Company(
            company_name=data['company_name'],
            email=data['email'],
            phone_number=data['phone_number'],
            prefix=prefix
        )
        company.set_password(data['password'])
        
        # Save to database
        db.session.add(company)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful',
            'company_id': company.id,
            'prefix': prefix
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/add_product', methods=['POST'])
@jwt_required()
def api_add_product():
    """API endpoint for adding products"""
    try:
        company_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Generate unique product hash
        product_hash = generate_product_hash(data['product_name'])
        
        # Create new product
        product = Product(
            product_name=data['product_name'],
            description=data.get('description', ''),
            image_url=data.get('image_url'),
            product_hash=product_hash,
            company_id=company_id
        )
        
        # Generate QR code
        qr_code_path = create_qr_code_path(company.prefix, product_hash)
        generate_qr_code(company.prefix, product_hash, qr_code_path)
        product.qr_code_path = qr_code_path
        
        # Save to database
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product added successfully',
            'product': product.to_dict(),
            'qr_url': url_for('generate_qr_route', product_hash=product_hash, _external=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error adding product: {str(e)}'}), 500

# Admin Routes

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('admin/login.html')
        
        # Find admin by username
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            from flask import session
            from datetime import datetime
            
            # Update last login
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create session
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session['is_super_admin'] = admin.is_super_admin
            
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    from flask import session
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('is_super_admin', None)
    flash('Admin logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    from flask import session
    from sqlalchemy import func
    
    if 'admin_id' not in session:
        flash('Please login to access admin dashboard', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        # Get statistics
        total_companies = Company.query.count()
        verified_companies = Company.query.filter_by(is_verified=True).count()
        total_products = Product.query.count()
        
        # Get recent companies (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_companies = Company.query.filter(Company.created_at >= thirty_days_ago).count()
        
        # Get top companies by product count
        top_companies = db.session.query(
            Company.company_name,
            Company.prefix,
            Company.email,
            Company.is_verified,
            Company.created_at,
            func.count(Product.id).label('product_count')
        ).outerjoin(Product).group_by(Company.id).order_by(func.count(Product.id).desc()).limit(10).all()
        
        # Get recent products
        recent_products = db.session.query(Product, Company).join(Company).order_by(Product.created_at.desc()).limit(10).all()
        
        stats = {
            'total_companies': total_companies,
            'verified_companies': verified_companies,
            'total_products': total_products,
            'recent_companies': recent_companies,
            'verification_rate': (verified_companies / total_companies * 100) if total_companies > 0 else 0
        }
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             top_companies=top_companies,
                             recent_products=recent_products)
        
    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/companies')
def admin_companies():
    """Admin companies list"""
    from flask import session
    
    if 'admin_id' not in session:
        flash('Please login to access admin panel', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        companies = Company.query.order_by(Company.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/companies.html', companies=companies)
        
    except Exception as e:
        flash(f'Error loading companies: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/company/<int:company_id>')
def admin_company_detail(company_id):
    """Admin company detail view"""
    from flask import session
    
    if 'admin_id' not in session:
        flash('Please login to access admin panel', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        company = Company.query.get_or_404(company_id)
        products = Product.query.filter_by(company_id=company_id).order_by(Product.created_at.desc()).all()
        
        return render_template('admin/company_detail.html', company=company, products=products)
        
    except Exception as e:
        flash(f'Error loading company details: {str(e)}', 'error')
        return redirect(url_for('admin_companies'))

@app.route('/admin/company/<int:company_id>/toggle-verification', methods=['POST'])
def admin_toggle_verification(company_id):
    """Toggle company verification status"""
    from flask import session
    
    if 'admin_id' not in session:
        flash('Please login to access admin panel', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        company = Company.query.get_or_404(company_id)
        company.is_verified = not company.is_verified
        db.session.commit()
        
        status = "verified" if company.is_verified else "unverified"
        flash(f'Company {company.company_name} has been {status}', 'success')
        
        return redirect(url_for('admin_company_detail', company_id=company_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating verification status: {str(e)}', 'error')
        return redirect(url_for('admin_company_detail', company_id=company_id))

@app.route('/admin/company/<int:company_id>/delete', methods=['POST'])
def admin_delete_company(company_id):
    """Delete company and all associated data"""
    from flask import session
    import os
    
    if 'admin_id' not in session:
        flash('Please login to access admin panel', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        company = Company.query.get_or_404(company_id)
        company_name = company.company_name
        
        # Get all products for this company to clean up files
        products = Product.query.filter_by(company_id=company_id).all()
        
        # Delete product files (QR codes and images)
        for product in products:
            # Delete QR code file
            if product.qr_code_path and os.path.exists(product.qr_code_path):
                try:
                    os.remove(product.qr_code_path)
                except OSError:
                    pass  # File might not exist or be accessible
            
            # Delete product image if it's in our uploads folder
            if product.image_url and 'uploads/' in product.image_url:
                try:
                    # Extract filename from URL
                    filename = product.image_url.split('/')[-1]
                    image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except OSError:
                    pass
        
        # Delete company document
        if company.document_path and os.path.exists(company.document_path):
            try:
                os.remove(company.document_path)
            except OSError:
                pass
        
        # Delete all products first (foreign key constraint)
        Product.query.filter_by(company_id=company_id).delete()
        
        # Delete the company
        db.session.delete(company)
        db.session.commit()
        
        flash(f'Company "{company_name}" and all associated data have been permanently deleted', 'success')
        return redirect(url_for('admin_companies'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting company: {str(e)}', 'error')
        return redirect(url_for('admin_company_detail', company_id=company_id))

@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html', error='Internal server error'), 500
