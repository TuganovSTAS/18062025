import hashlib
import qrcode
import os
from datetime import datetime
from PIL import Image
from flask import current_app, url_for

def generate_product_hash(product_name, timestamp=None):
    """Generate unique product hash using SHA256"""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    # Create hash from product name and timestamp
    hash_input = f"{product_name}{timestamp}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()

def generate_qr_code(company_prefix, product_hash, save_path=None):
    """Generate QR code for product"""
    # Create the URL that the QR code will point to
    qr_url = f"http://localhost:5000/product/{company_prefix}/{product_hash}"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code if path is provided
    if save_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        qr_img.save(save_path)
        return save_path
    
    return qr_img

def allowed_file(filename, allowed_extensions=None):
    """Check if file has allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder, filename=None):
    """Save uploaded file and return the path"""
    if filename is None:
        filename = file.filename
    
    # Create unique filename to avoid conflicts
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + filename
    
    file_path = os.path.join(upload_folder, filename)
    
    # Ensure directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    file.save(file_path)
    
    return file_path

def create_qr_code_path(company_prefix, product_hash):
    """Create standardized QR code file path"""
    filename = f"{company_prefix}_{product_hash}.png"
    return os.path.join(current_app.config["QR_FOLDER"], filename)
