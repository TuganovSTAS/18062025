import os
import logging
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_babel import Babel, get_locale
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///qr_platform.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # Tokens don't expire for demo

# Configure file uploads
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["QR_FOLDER"] = "static/qr_codes"

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
babel = Babel()

# Supported languages
LANGUAGES = {
    'en': 'English',
    'ru': 'Русский'
}

def get_locale():
    # 1. Check if language is forced in URL args
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')
    
    # 2. Check session
    if 'language' in session and session['language'] in LANGUAGES.keys():
        return session['language']
    
    # 3. Check browser accept languages
    return request.accept_languages.best_match(LANGUAGES.keys()) or 'en'

babel.init_app(app, locale_selector=get_locale)

# Create upload directories
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["QR_FOLDER"], exist_ok=True)

with app.app_context():
    # Import models and routes
    import models  # noqa: F401
    import routes  # noqa: F401
    
    # Create all database tables
    db.create_all()
    
    # Make LANGUAGES available in templates
    @app.context_processor
    def inject_conf_vars():
        return {
            'LANGUAGES': LANGUAGES,
            'CURRENT_LANGUAGE': get_locale()
        }
    
    logging.info("Database tables created successfully")
