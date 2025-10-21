from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

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
        
        from app.models import user, session as session_model, item, response, snapshot, recommendation, audit
        
        db.create_all()
        
        if app.config['SEED_ON_START']:
            from app.core.utils import seed_database
            seed_database()
    
    return app
