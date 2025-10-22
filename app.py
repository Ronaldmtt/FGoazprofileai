from app import create_app, db
import os

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Development mode only
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
