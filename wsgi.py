from app import create_app, db
import os

# Create Flask app instance for Gunicorn
app = create_app()

# Initialize database tables
def init_db():
    """Initialize database tables if needed."""
    with app.app_context():
        db.create_all()

# Initialize DB on startup
init_db()

if __name__ == '__main__':
    # Development mode only - when running directly with python app.py
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
