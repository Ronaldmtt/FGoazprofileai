from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session, current_app
from app.core.security import validate_email_domain
from app.models import User, Audit
from app import db
from datetime import datetime
from config import Config
from app.services.logger import auth_logger

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/')
def index():
    """Redirect root to login page."""
    auth_logger.event_info('auth_redirect_to_login')
    return redirect(url_for('auth.login_page'))

@bp.route('/login', methods=['GET'])
def login_page():
    """Render login page."""
    auth_logger.event_start('login_page_load')
    flask_session.clear()
    auth_logger.event_success('login_page_load')
    auth_logger.event_end('login_page_load')
    return render_template('login.html')

@bp.route('/magic-link', methods=['POST'])
def magic_link():
    """Direct login with email domain validation."""
    auth_logger.event_start('magic_link_login')
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        auth_logger.event_info('magic_link_login', {'email': email})
        
        if not validate_email_domain(email, Config.ALLOWED_EMAIL_DOMAINS):
            domains = ', @'.join(Config.ALLOWED_EMAIL_DOMAINS)
            auth_logger.event_error('magic_link_login', details={'reason': 'invalid_domain', 'email': email})
            auth_logger.event_end('magic_link_login')
            return jsonify({
                'error': f'Email deve ser de um dos domínios: @{domains}'
            }), 400
        
        audit = Audit(
            actor=email,
            action='login_attempt',
            target='auth',
            payload={'email': email}
        )
        db.session.add(audit)
        db.session.commit()
        
        user = User.query.filter_by(email=email).first()
        
        if user:
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
            
            auth_logger.event_success('magic_link_login', {'user_id': user.id, 'email': email, 'is_new_user': False})
            auth_logger.event_end('magic_link_login')
            
            return jsonify({
                'success': True,
                'redirect': url_for('session.start_page')
            })
        else:
            flask_session['pending_email'] = email
            
            auth_logger.event_info('magic_link_login', {'email': email, 'action': 'redirect_to_consent', 'is_new_user': True})
            auth_logger.event_end('magic_link_login')
            
            return jsonify({
                'success': True,
                'redirect': url_for('auth.consent')
            })
    
    except Exception as e:
        auth_logger.event_error('magic_link_login', error=e)
        auth_logger.event_end('magic_link_login')
        return jsonify({'error': 'Erro ao fazer login'}), 500

@bp.route('/consent', methods=['GET', 'POST'])
def consent():
    """Handle LGPD consent for new users."""
    auth_logger.event_start('consent_flow')
    email = flask_session.get('pending_email')
    
    if not email:
        auth_logger.event_error('consent_flow', details={'reason': 'no_pending_email'})
        auth_logger.event_end('consent_flow')
        return render_template('error.html',
            message='Sessão inválida. Por favor, faça login novamente.'), 400
    
    if request.method == 'GET':
        auth_logger.event_info('consent_flow', {'action': 'show_consent_page', 'email': email})
        auth_logger.event_end('consent_flow')
        return render_template('consent.html', email=email)
    
    auth_logger.event_info('consent_flow', {'action': 'process_consent_form', 'email': email})
    
    consent_given = request.form.get('consent') == 'true'
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    role = request.form.get('role', '').strip()
    
    if not consent_given:
        auth_logger.event_error('consent_flow', details={'reason': 'consent_not_given', 'email': email})
        auth_logger.event_end('consent_flow')
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
    flask_session.pop('pending_email', None)
    
    audit = Audit(
        actor=email,
        action='user_created',
        target='users',
        payload={'user_id': user.id, 'consent': True}
    )
    db.session.add(audit)
    db.session.commit()
    
    auth_logger.event_success('consent_flow', {'user_id': user.id, 'email': email})
    auth_logger.event_end('consent_flow')
    
    return redirect(url_for('session.start_page'))

@bp.route('/logout', methods=['GET'])
def logout():
    """Logout user."""
    auth_logger.event_start('user_logout')
    user_id = flask_session.get('user_id', 'unknown')
    email = flask_session.get('email', 'unknown')
    flask_session.clear()
    auth_logger.event_success('user_logout', {'user_id': user_id, 'email': email})
    auth_logger.event_end('user_logout')
    return redirect(url_for('auth.login_page'))
