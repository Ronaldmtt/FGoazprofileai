from flask import Blueprint, request, jsonify, render_template, send_file, session as flask_session, redirect, url_for
from app.models import User, Session, Item, Response, ProficiencySnapshot
from app.agents.content_qa import AgentContentQA
from app.services.exporter import export_to_csv, export_to_xlsx
from app.core.utils import log_audit
from app.core.scoring import IRTScorer
from app import db
from sqlalchemy import func
import json
import os

bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin(f):
    """Decorator to require admin authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask_session.get('is_admin'):
            return redirect(url_for('admin.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET'])
def login_page():
    """Admin login page."""
    return render_template('admin/login.html')

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate admin user."""
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    # Get admin credentials from environment
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    
    if not admin_password:
        return jsonify({'error': 'Credenciais de admin não configuradas'}), 500
    
    if username == admin_username and password == admin_password:
        flask_session['is_admin'] = True
        flask_session['admin_username'] = username
        
        log_audit(
            actor=username,
            action='admin_login',
            target='admin',
            payload={}
        )
        
        return jsonify({'success': True, 'redirect': url_for('admin.dashboard')})
    
    return jsonify({'error': 'Usuário ou senha incorretos'}), 401

@bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logout admin user."""
    flask_session.pop('is_admin', None)
    flask_session.pop('admin_username', None)
    return redirect(url_for('admin.login_page'))

@bp.route('/dashboard', methods=['GET'])
@require_admin
def dashboard():
    """Admin dashboard with overview metrics."""
    return render_template('admin/dashboard.html')

@bp.route('/overview', methods=['GET'])
@require_admin
def overview():
    """Get overview metrics for dashboard."""
    total_users = User.query.count()
    total_sessions = Session.query.count()
    completed_sessions = Session.query.filter_by(status='completed').count()
    active_sessions = Session.query.filter_by(status='active').count()
    
    irt = IRTScorer()
    
    level_distribution = {}
    for level in ['N0', 'N1', 'N2', 'N3', 'N4', 'N5']:
        level_distribution[level] = 0
    
    completed_session_ids = [s.id for s in Session.query.filter_by(status='completed').all()]
    
    for session_id in completed_session_ids:
        snapshots = ProficiencySnapshot.query.filter_by(session_id=session_id).all()
        if snapshots:
            scores = {s.competency: s.score_0_100 for s in snapshots}
            global_score = irt.calculate_global_score(scores)
            level = irt.calculate_level(global_score)
            level_distribution[level] += 1
    
    participation_rate = (completed_sessions / total_users * 100) if total_users > 0 else 0
    
    return jsonify({
        'total_users': total_users,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'active_sessions': active_sessions,
        'participation_rate': round(participation_rate, 1),
        'level_distribution': level_distribution
    })

@bp.route('/heatmap', methods=['GET'])
@require_admin
def heatmap():
    """Get competency heatmap data."""
    group_by = request.args.get('group_by', 'all')
    
    from config import Config
    
    competency_stats = {}
    for comp in Config.COMPETENCIES:
        competency_stats[comp] = {
            'avg_score': 0,
            'count': 0
        }
    
    if group_by == 'all':
        for comp in Config.COMPETENCIES:
            snapshots = ProficiencySnapshot.query.filter_by(competency=comp).all()
            if snapshots:
                avg = sum(s.score_0_100 for s in snapshots) / len(snapshots)
                competency_stats[comp] = {
                    'avg_score': round(avg, 1),
                    'count': len(snapshots)
                }
    
    elif group_by == 'department':
        departments = db.session.query(User.department).distinct().all()
        department_data = {}
        
        for (dept,) in departments:
            if not dept:
                continue
            department_data[dept] = {}
            
            user_ids = [u.id for u in User.query.filter_by(department=dept).all()]
            session_ids = [s.id for s in Session.query.filter(
                Session.user_id.in_(user_ids),
                Session.status == 'completed'
            ).all()]
            
            for comp in Config.COMPETENCIES:
                snapshots = ProficiencySnapshot.query.filter(
                    ProficiencySnapshot.session_id.in_(session_ids),
                    ProficiencySnapshot.competency == comp
                ).all()
                
                if snapshots:
                    avg = sum(s.score_0_100 for s in snapshots) / len(snapshots)
                    department_data[dept][comp] = round(avg, 1)
                else:
                    department_data[dept][comp] = 0
        
        return jsonify(department_data)
    
    return jsonify(competency_stats)

@bp.route('/users', methods=['GET'])
@require_admin
def users_list():
    """List all users with their assessment results."""
    return render_template('admin/users.html')

@bp.route('/users/data', methods=['GET'])
@require_admin
def users_data():
    """Get list of all users with their scores."""
    users = User.query.all()
    irt = IRTScorer()
    
    users_list = []
    for user in users:
        # Get the most recent completed session
        session = Session.query.filter_by(
            user_id=user.id, 
            status='completed'
        ).order_by(Session.ended_at.desc()).first()
        
        if session:
            snapshots = ProficiencySnapshot.query.filter_by(session_id=session.id).all()
            scores = {s.competency: s.score_0_100 for s in snapshots}
            
            global_score = irt.calculate_global_score(scores)
            global_level = irt.calculate_level(global_score)
            
            users_list.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'department': user.department or 'N/A',
                'role': user.role or 'N/A',
                'global_score': round(global_score, 1),
                'global_level': global_level,
                'completed_at': session.ended_at.isoformat() if session.ended_at else None,
                'time_spent_s': session.time_spent_s
            })
        else:
            # User registered but hasn't completed assessment
            users_list.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'department': user.department or 'N/A',
                'role': user.role or 'N/A',
                'global_score': None,
                'global_level': 'Pendente',
                'completed_at': None,
                'time_spent_s': None
            })
    
    return jsonify(users_list)

@bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def user_detail(user_id):
    """Get detailed information about a user."""
    user = User.query.get_or_404(user_id)
    sessions = Session.query.filter_by(user_id=user_id, status='completed').all()
    
    session_data = []
    for sess in sessions:
        snapshots = ProficiencySnapshot.query.filter_by(session_id=sess.id).all()
        scores = {s.competency: s.score_0_100 for s in snapshots}
        
        irt = IRTScorer()
        global_score = irt.calculate_global_score(scores)
        global_level = irt.calculate_level(global_score)
        
        session_data.append({
            'id': sess.id,
            'started_at': sess.started_at.isoformat(),
            'ended_at': sess.ended_at.isoformat() if sess.ended_at else None,
            'time_spent_s': sess.time_spent_s,
            'global_score': round(global_score, 1),
            'global_level': global_level,
            'competency_scores': scores
        })
    
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'department': user.department,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        },
        'sessions': session_data
    })

@bp.route('/items', methods=['GET'])
@require_admin
def list_items():
    """List all assessment items."""
    items = Item.query.all()
    
    items_data = []
    for item in items:
        items_data.append({
            'id': item.id,
            'stem': item.stem[:100] + '...' if len(item.stem) > 100 else item.stem,
            'type': item.type,
            'competency': item.competency,
            'difficulty_b': item.difficulty_b,
            'discrimination_a': item.discrimination_a,
            'active': item.active,
            'tags': item.tags
        })
    
    return jsonify(items_data)

@bp.route('/items', methods=['POST'])
@require_admin
def create_item():
    """Create new assessment item with validation."""
    data = request.get_json()
    
    content_qa = AgentContentQA()
    validation = content_qa.validate_item(data)
    
    if not validation['valid']:
        return jsonify({
            'error': 'Item inválido',
            'issues': validation['issues']
        }), 400
    
    item = Item(
        stem=data['stem'],
        type=data['type'],
        competency=data['competency'],
        difficulty_b=data.get('difficulty_b', 1.0),
        discrimination_a=data.get('discrimination_a', 0.5),
        tags=data.get('tags', ''),
        active=data.get('active', True)
    )
    
    if data.get('choices'):
        item.choices = data['choices']
    if data.get('answer_key'):
        item.answer_key = data['answer_key']
    if data.get('rubric'):
        item.rubric = data['rubric']
    
    db.session.add(item)
    db.session.commit()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='item_created',
        target='items',
        payload={'item_id': item.id}
    )
    
    return jsonify({
        'message': 'Item criado com sucesso',
        'item_id': item.id
    }), 201

@bp.route('/items/<int:item_id>', methods=['PUT'])
@require_admin
def update_item(item_id):
    """Update existing assessment item."""
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    content_qa = AgentContentQA()
    validation = content_qa.validate_item(data)
    
    if not validation['valid']:
        return jsonify({
            'error': 'Item inválido',
            'issues': validation['issues']
        }), 400
    
    if 'stem' in data:
        item.stem = data['stem']
    if 'type' in data:
        item.type = data['type']
    if 'competency' in data:
        item.competency = data['competency']
    if 'difficulty_b' in data:
        item.difficulty_b = data['difficulty_b']
    if 'discrimination_a' in data:
        item.discrimination_a = data['discrimination_a']
    if 'tags' in data:
        item.tags = data['tags']
    if 'active' in data:
        item.active = data['active']
    if 'choices' in data:
        item.choices = data['choices']
    if 'answer_key' in data:
        item.answer_key = data['answer_key']
    if 'rubric' in data:
        item.rubric = data['rubric']
    
    db.session.commit()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='item_updated',
        target='items',
        payload={'item_id': item.id}
    )
    
    return jsonify({'message': 'Item atualizado com sucesso'})

@bp.route('/items/<int:item_id>', methods=['DELETE'])
@require_admin
def delete_item(item_id):
    """Delete (deactivate) assessment item."""
    item = Item.query.get_or_404(item_id)
    
    item.active = False
    db.session.commit()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='item_deleted',
        target='items',
        payload={'item_id': item.id}
    )
    
    return jsonify({'message': 'Item desativado com sucesso'})

@bp.route('/export.csv', methods=['GET'])
@require_admin
def export_csv():
    """Export assessment results to CSV."""
    filepath = export_to_csv()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='export_csv',
        target='data',
        payload={}
    )
    
    return send_file(filepath, as_attachment=True, download_name='oaz_profiler_export.csv')

@bp.route('/export.xlsx', methods=['GET'])
@require_admin
def export_xlsx():
    """Export assessment results to Excel."""
    filepath = export_to_xlsx()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='export_xlsx',
        target='data',
        payload={}
    )
    
    return send_file(filepath, as_attachment=True, download_name='oaz_profiler_export.xlsx')
