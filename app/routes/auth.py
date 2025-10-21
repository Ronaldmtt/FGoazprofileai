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
    """Generate magic link for email authentication."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not validate_email_domain(email, Config.ALLOWED_EMAIL_DOMAIN):
            return jsonify({
                'error': f'Email deve ser do domínio @{Config.ALLOWED_EMAIL_DOMAIN}'
            }), 400
        
        token = generate_token(email)
        magic_url = f"{Config.BASE_URL}/auth/verify?token={token}"
        
        logger.info(f"Magic link generated for {email}")
        logger.info(f"Magic link URL (DEV): {magic_url}")
        print(f"\n{'='*60}\nMAGIC LINK for {email}:\n{magic_url}\n{'='*60}\n")
        
        audit = Audit(
            actor=email,
            action='magic_link_requested',
            target='auth',
            payload={'email': email}
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'message': 'Link de acesso enviado! Verifique o console (modo dev).',
            'dev_link': magic_url if current_app.config.get('FLASK_ENV') == 'development' else None
        })
    
    except Exception as e:
        logger.error(f"Error generating magic link: {str(e)}")
        return jsonify({'error': 'Erro ao gerar link de acesso'}), 500

@bp.route('/verify', methods=['GET'])
def verify():
    """Verify magic link token and create/login user."""
    token = request.args.get('token')
    
    if not token:
        return "Token inválido", 400
    
    email = verify_token(token, max_age=Config.TOKEN_EXPIRATION_HOURS * 3600)
    
    if not email:
        return render_template('error.html', 
            message='Link expirado ou inválido. Por favor, solicite um novo.')
    
    if not validate_email_domain(email, Config.ALLOWED_EMAIL_DOMAIN):
        return render_template('error.html',
            message=f'Email deve ser do domínio @{Config.ALLOWED_EMAIL_DOMAIN}')
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('auth.consent', token=token))
    
    flask_session['user_id'] = user.id
    flask_session['email'] = user.email
    
    audit = Audit(
        actor=email,
        action='login',
        target='auth',
        payload={'user_id': user.id}
    )
    db.session.add(audit)
    db.session.commit()
    
    return redirect(url_for('session.start_page'))

@bp.route('/consent', methods=['GET', 'POST'])
def consent():
    """Handle LGPD consent for new users."""
    token = request.args.get('token')
    
    if not token:
        return "Token inválido", 400
    
    email = verify_token(token, max_age=Config.TOKEN_EXPIRATION_HOURS * 3600)
    
    if not email:
        return "Link expirado", 400
    
    if request.method == 'GET':
        return render_template('consent.html', email=email, token=token)
    
    consent = request.form.get('consent') == 'true'
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    role = request.form.get('role', '').strip()
    
    if not consent:
        return render_template('error.html',
            message='É necessário aceitar os termos para continuar.')
    
    user = User(
        email=email,
        name=name if name else None,
        department=department if department else None,
        role=role if role else None,
        consent_ts=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    
    flask_session['user_id'] = user.id
    flask_session['email'] = user.email
    
    audit = Audit(
        actor=email,
        action='user_created',
        target='users',
        payload={'user_id': user.id, 'consent': True}
    )
    db.session.add(audit)
    db.session.commit()
    
    return redirect(url_for('session.start_page'))

@bp.route('/logout', methods=['GET'])
def logout():
    """Logout user."""
    flask_session.clear()
    return redirect(url_for('auth.login_page'))
