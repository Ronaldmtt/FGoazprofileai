from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
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
        
        db.create_all()
        
        if app.config['SEED_ON_START']:
            from app.core.utils import seed_database
            seed_database()
    
    return app
