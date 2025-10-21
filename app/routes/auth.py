from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session, current_app
from app.core.security import generate_token, verify_token, validate_email_domain
from app.core.schemas import MagicLinkRequest
from app.models import User, Audit
from app import db
from datetime import datetime
from config import Config
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Redirect root to login page."""
    return redirect(url_for('auth.login_page'))

@bp.route('/login', methods=['GET'])
def login_page():
    """Render login page."""
    return render_template('login.html')

@bp.route('/magic-link', methods=['POST'])
def magic_link():
    """Direct login with email domain validation."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not validate_email_domain(email, Config.ALLOWED_EMAIL_DOMAIN):
            return jsonify({
                'error': f'Email deve ser do domínio @{Config.ALLOWED_EMAIL_DOMAIN}'
            }), 400
        
        # Log login attempt
        audit = Audit(
            actor=email,
            action='login_attempt',
            target='auth',
            payload={'email': email}
        )
        db.session.add(audit)
        db.session.commit()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Existing user - login directly
            flask_session['user_id'] = user.id
            flask_session['email'] = user.email
            
            audit = Audit(
                actor=email,
                action='login_success',
                target='auth',
                payload={'user_id': user.id}
            )
            db.session.add(audit)
            db.session.commit()
            
            logger.info(f"User {email} logged in successfully")
            
            return jsonify({
                'success': True,
                'redirect': url_for('session.start_page')
            })
        else:
            # New user - needs consent
            flask_session['pending_email'] = email
            
            logger.info(f"New user {email} - redirecting to consent")
            
            return jsonify({
                'success': True,
                'redirect': url_for('auth.consent')
            })
    
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Erro ao fazer login'}), 500

@bp.route('/consent', methods=['GET', 'POST'])
def consent():
    """Handle LGPD consent for new users."""
    # Get email from session
    email = flask_session.get('pending_email')
    
    if not email:
        return render_template('error.html',
            message='Sessão inválida. Por favor, faça login novamente.'), 400
    
    if request.method == 'GET':
        return render_template('consent.html', email=email)
    
    consent = request.form.get('consent') == 'true'
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    role = request.form.get('role', '').strip()
    
    if not consent:
        return render_template('error.html',
            message='É necessário aceitar os termos para continuar.')
    
    # Create new user
    user = User(
        email=email,
        name=name if name else None,
        department=department if department else None,
        role=role if role else None,
        consent_ts=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    
    # Set user session
    flask_session['user_id'] = user.id
    flask_session['email'] = user.email
    flask_session.pop('pending_email', None)  # Clear pending email
    
    # Audit log
    audit = Audit(
        actor=email,
        action='user_created',
        target='users',
        payload={'user_id': user.id, 'consent': True}
    )
    db.session.add(audit)
    db.session.commit()
    
    logger.info(f"User {email} created with consent")
    
    return redirect(url_for('session.start_page'))

@bp.route('/logout', methods=['GET'])
def logout():
    """Logout user."""
    flask_session.clear()
    return redirect(url_for('auth.login_page'))
