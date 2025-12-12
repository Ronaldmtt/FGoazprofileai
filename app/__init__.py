from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging
import os

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

db = SQLAlchemy()

def _init_rpa_monitor():
    """Initialize RPA Monitor client from environment variables."""
    try:
        from rpa_monitor_client import setup_rpa_monitor
        
        rpa_id = os.environ.get('RPA_MONITOR_ID')
        host = os.environ.get('RPA_MONITOR_HOST')
        region = os.environ.get('RPA_MONITOR_REGION', 'default')
        transport = os.environ.get('RPA_MONITOR_TRANSPORT', 'ws')
        
        logging.info(f"RPA Monitor config: id={rpa_id}, host={host}, region={region}, transport={transport}")
        
        if rpa_id and host:
            setup_rpa_monitor(
                rpa_id=rpa_id,
                host=host,
                port=None,
                region=region,
                transport=transport,
            )
            logging.info(f"RPA Monitor initialized: {rpa_id} -> {host}")
        else:
            logging.warning("RPA Monitor not configured - missing RPA_MONITOR_ID or RPA_MONITOR_HOST")
    except Exception as e:
        logging.error(f"Failed to initialize RPA Monitor: {e}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize RPA Monitor
    _init_rpa_monitor()
    
    db.init_app(app)
    
    @app.template_filter('chr')
    def chr_filter(value):
        """Convert number to ASCII character (0->A, 1->B, etc.)"""
        return chr(65 + int(value))
    
    with app.app_context():
        from app.routes import auth, session, items, responses, admin
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(session.bp)
        app.register_blueprint(items.bp)
        app.register_blueprint(responses.bp)
        app.register_blueprint(admin.bp)
        
        @app.route('/')
        def index():
            from flask import redirect, url_for
            return redirect(url_for('auth.login_page'))
        
        @app.route('/health')
        def health_check():
            """Health check endpoint for deployment."""
            return {'status': 'healthy', 'service': 'oaz-ia-profiler'}, 200
        
        from app.models import user, session as session_model, item, response, snapshot, recommendation, audit
        
        # Create all tables FIRST with new schema
        db.create_all()
        
        # THEN seed database (after tables exist)
        if app.config.get('SEED_ON_START', False):
            from app.core.utils import seed_database
            seed_database()
    
    return app
