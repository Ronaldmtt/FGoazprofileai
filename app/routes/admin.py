from flask import Blueprint, request, jsonify, render_template, send_file, session as flask_session, redirect, url_for
from app.models import User, Session, Item, Response, ProficiencySnapshot
from app.agents.content_qa import AgentContentQA
from app.services.exporter import export_to_csv, export_to_xlsx
from app.services.analytics import get_global_stats, get_frente_stats, get_department_stats, get_role_stats, get_complete_dashboard_data
from app.services.logger import admin_logger, export_logger
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
    admin_logger.event_start('admin_login_page_load')
    admin_logger.event_success('admin_login_page_load')
    return render_template('admin/login.html')

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate admin user."""
    admin_logger.event_start('admin_login_attempt')
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    admin_logger.event_info('admin_login_attempt', {'username': username})
    
    admin_username = os.environ.get('ADMIN_LOGIN', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    
    if not admin_password:
        admin_logger.event_error('admin_login_attempt', details={'reason': 'credentials_not_configured'})
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
        
        admin_logger.event_success('admin_login_attempt', {'username': username})
        admin_logger.event_end('admin_login_attempt')
        return jsonify({'success': True, 'redirect': url_for('admin.dashboard')})
    
    admin_logger.event_error('admin_login_attempt', details={'reason': 'invalid_credentials', 'username': username})
    admin_logger.event_end('admin_login_attempt')
    return jsonify({'error': 'Usuário ou senha incorretos'}), 401

@bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logout admin user."""
    admin_logger.event_start('admin_logout')
    username = flask_session.get('admin_username', 'unknown')
    flask_session.pop('is_admin', None)
    flask_session.pop('admin_username', None)
    admin_logger.event_success('admin_logout', {'username': username})
    admin_logger.event_end('admin_logout')
    return redirect(url_for('admin.login_page'))

@bp.route('/dashboard', methods=['GET'])
@require_admin
def dashboard():
    """Admin dashboard with overview metrics."""
    admin_logger.event_start('dashboard_load')
    admin_logger.event_success('dashboard_load')
    admin_logger.event_end('dashboard_load')
    return render_template('admin/dashboard.html')

@bp.route('/overview', methods=['GET'])
@require_admin
def overview():
    """Get overview metrics for dashboard (matrix-based)."""
    admin_logger.event_start('overview_metrics_load')
    
    total_users = User.query.count()
    total_sessions = Session.query.count()
    completed_sessions = Session.query.filter_by(status='completed').count()
    active_sessions = Session.query.filter_by(status='active').count()
    
    level_distribution = {
        'Iniciante': 0,
        'Explorador': 0,
        'Praticante': 0,
        'Líder Digital': 0
    }
    
    snapshots = ProficiencySnapshot.query.all()
    for snapshot in snapshots:
        if snapshot.maturity_level and snapshot.maturity_level in level_distribution:
            level_distribution[snapshot.maturity_level] += 1
    
    participation_rate = (completed_sessions / total_users * 100) if total_users > 0 else 0
    
    admin_logger.event_success('overview_metrics_load', {
        'total_users': total_users,
        'completed_sessions': completed_sessions
    })
    admin_logger.event_end('overview_metrics_load')
    
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
    """Get block heatmap data (matrix-based)."""
    admin_logger.event_start('heatmap_data_load')
    from app.core.blocks_config import BLOCKS
    
    group_by = request.args.get('group_by', 'all')
    admin_logger.event_info('heatmap_data_load', {'group_by': group_by})
    
    if group_by == 'all':
        # Get average scores per block across all users
        block_stats = {}
        
        for block_name in BLOCKS.keys():
            # Get all snapshots and calculate average score for this block
            snapshots = ProficiencySnapshot.query.all()
            block_scores = []
            
            for snapshot in snapshots:
                if snapshot.block_scores and block_name in snapshot.block_scores:
                    block_scores.append(snapshot.block_scores[block_name])
            
            if block_scores:
                avg_score = sum(block_scores) / len(block_scores)
                block_stats[block_name] = {
                    'avg_score': round(avg_score, 1),
                    'count': len(block_scores)
                }
            else:
                block_stats[block_name] = {
                    'avg_score': 0,
                    'count': 0
                }
        
        admin_logger.event_success('heatmap_data_load', {'group_by': 'all'})
        admin_logger.event_end('heatmap_data_load')
        return jsonify(block_stats)
    
    elif group_by == 'department':
        # Get scores grouped by department
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
            
            snapshots = ProficiencySnapshot.query.filter(
                ProficiencySnapshot.session_id.in_(session_ids)
            ).all()
            
            for block_name in BLOCKS.keys():
                block_scores = []
                for snapshot in snapshots:
                    if snapshot.block_scores and block_name in snapshot.block_scores:
                        block_scores.append(snapshot.block_scores[block_name])
                
                if block_scores:
                    department_data[dept][block_name] = round(sum(block_scores) / len(block_scores), 1)
                else:
                    department_data[dept][block_name] = 0
        
        admin_logger.event_success('heatmap_data_load', {'group_by': 'department'})
        admin_logger.event_end('heatmap_data_load')
        return jsonify(department_data)
    
    admin_logger.event_end('heatmap_data_load')
    return jsonify({})

@bp.route('/users', methods=['GET'])
@require_admin
def users_list():
    """List all users with their assessment results."""
    admin_logger.event_start('users_list_page_load')
    admin_logger.event_success('users_list_page_load')
    admin_logger.event_end('users_list_page_load')
    return render_template('admin/users.html')

@bp.route('/users/data', methods=['GET'])
@require_admin
def users_data():
    """Get list of all users with their scores (matrix-based)."""
    admin_logger.event_start('users_data_load')
    users = User.query.all()
    admin_logger.event_info('users_data_load', {'total_users': len(users)})
    
    users_list = []
    for user in users:
        # Get the most recent completed session
        session = Session.query.filter_by(
            user_id=user.id, 
            status='completed'
        ).order_by(Session.ended_at.desc()).first()
        
        if session:
            snapshot = ProficiencySnapshot.query.filter_by(session_id=session.id).first()
            
            if snapshot:
                users_list.append({
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'department': user.department or 'N/A',
                    'role': user.role or 'N/A',
                    'raw_score': snapshot.raw_score,
                    'maturity_level': snapshot.maturity_level or 'N/A',
                    'completed_at': session.ended_at.isoformat() if session.ended_at else None,
                    'time_spent_s': session.time_spent_s
                })
            else:
                users_list.append({
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'department': user.department or 'N/A',
                    'role': user.role or 'N/A',
                    'raw_score': None,
                    'maturity_level': 'Sem dados',
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
                'raw_score': None,
                'maturity_level': 'Pendente',
                'completed_at': None,
                'time_spent_s': None
            })
    
    admin_logger.event_success('users_data_load', {'count': len(users_list)})
    admin_logger.event_end('users_data_load')
    return jsonify(users_list)

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Delete a user and all related data."""
    admin_logger.event_start('delete_user', {'user_id': user_id})
    user = User.query.get_or_404(user_id)
    user_email = user.email
    
    admin_logger.event_info('delete_user', {'user_email': user_email})
    
    sessions = Session.query.filter_by(user_id=user_id).all()
    
    for sess in sessions:
        Response.query.filter_by(session_id=sess.id).delete()
        ProficiencySnapshot.query.filter_by(session_id=sess.id).delete()
    
    Session.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    log_audit(
        actor=flask_session.get('admin_username', 'admin'),
        action='user_deleted',
        target='users',
        payload={'user_id': user_id, 'user_email': user_email}
    )
    
    admin_logger.event_success('delete_user', {'user_id': user_id, 'user_email': user_email})
    admin_logger.event_end('delete_user')
    return jsonify({'message': 'Usuário e todos os dados relacionados foram deletados com sucesso'})

@bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def user_detail(user_id):
    """Get detailed information about a user (matrix-based)."""
    admin_logger.event_start('user_detail_load', {'user_id': user_id})
    user = User.query.get_or_404(user_id)
    sessions = Session.query.filter_by(user_id=user_id, status='completed').all()
    
    session_data = []
    for sess in sessions:
        snapshot = ProficiencySnapshot.query.filter_by(session_id=sess.id).first()
        
        if snapshot:
            session_data.append({
                'id': sess.id,
                'started_at': sess.started_at.isoformat(),
                'ended_at': sess.ended_at.isoformat() if sess.ended_at else None,
                'time_spent_s': sess.time_spent_s,
                'raw_score': snapshot.raw_score,
                'maturity_level': snapshot.maturity_level,
                'block_scores': snapshot.block_scores
            })
        else:
            session_data.append({
                'id': sess.id,
                'started_at': sess.started_at.isoformat(),
                'ended_at': sess.ended_at.isoformat() if sess.ended_at else None,
                'time_spent_s': sess.time_spent_s,
                'raw_score': None,
                'maturity_level': 'Sem dados',
                'block_scores': {}
            })
    
    admin_logger.event_success('user_detail_load', {'user_id': user_id})
    admin_logger.event_end('user_detail_load')
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
    admin_logger.event_start('list_items')
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
    
    admin_logger.event_success('list_items', {'count': len(items_data)})
    admin_logger.event_end('list_items')
    return jsonify(items_data)

@bp.route('/items', methods=['POST'])
@require_admin
def create_item():
    """Create new assessment item with validation."""
    admin_logger.event_start('create_item')
    data = request.get_json()
    
    admin_logger.event_info('create_item', {'action': 'validating_item'})
    content_qa = AgentContentQA()
    validation = content_qa.validate_item(data)
    
    if not validation['valid']:
        admin_logger.event_error('create_item', details={'reason': 'validation_failed', 'issues': validation['issues']})
        admin_logger.event_end('create_item')
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
    
    admin_logger.event_success('create_item', {'item_id': item.id})
    admin_logger.event_end('create_item')
    return jsonify({
        'message': 'Item criado com sucesso',
        'item_id': item.id
    }), 201

@bp.route('/items/<int:item_id>', methods=['PUT'])
@require_admin
def update_item(item_id):
    """Update existing assessment item."""
    admin_logger.event_start('update_item')
    admin_logger.event_info('update_item', {'item_id': item_id})
    
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    content_qa = AgentContentQA()
    validation = content_qa.validate_item(data)
    
    if not validation['valid']:
        admin_logger.event_error('update_item', details={'reason': 'validation_failed', 'item_id': item_id})
        admin_logger.event_end('update_item')
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
    
    admin_logger.event_success('update_item', {'item_id': item_id})
    admin_logger.event_end('update_item')
    return jsonify({'message': 'Item atualizado com sucesso'})

@bp.route('/items/<int:item_id>', methods=['DELETE'])
@require_admin
def delete_item(item_id):
    """Delete (deactivate) assessment item."""
    admin_logger.event_start('delete_item')
    admin_logger.event_info('delete_item', {'item_id': item_id})
    
    item = Item.query.get_or_404(item_id)
    
    item.active = False
    db.session.commit()
    
    log_audit(
        actor=flask_session.get('email', 'admin'),
        action='item_deleted',
        target='items',
        payload={'item_id': item.id}
    )
    
    admin_logger.event_success('delete_item', {'item_id': item_id})
    admin_logger.event_end('delete_item')
    return jsonify({'message': 'Item desativado com sucesso'})

@bp.route('/export.csv', methods=['GET'])
@require_admin
def export_csv():
    """Export assessment results to CSV with optional filters."""
    from flask import Response
    
    export_logger.event_start('export_csv')
    
    frente = request.args.get('frente')
    department = request.args.get('department')
    role = request.args.get('role')
    
    export_logger.event_info('export_csv', {'frente': frente, 'department': department, 'role': role})
    
    filepath = export_to_csv(frente=frente, department=department, role=role)
    
    filter_parts = []
    if frente:
        filter_parts.append(frente.lower())
    if department:
        filter_parts.append(department.lower().replace(' ', '_'))
    if role:
        filter_parts.append(role.lower().replace(' ', '_'))
    
    filename = 'oaz_profiler'
    if filter_parts:
        filename += '_' + '_'.join(filter_parts)
    filename += '.csv'
    
    log_audit(
        actor=flask_session.get('admin_username', 'admin'),
        action='export_csv',
        target='data',
        payload={'frente': frente, 'department': department, 'role': role}
    )
    
    with open(filepath, 'rb') as f:
        csv_content = f.read()
    
    response = Response(
        csv_content,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(csv_content)),
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        }
    )
    export_logger.event_success('export_csv', {'filename': filename, 'size': len(csv_content)})
    export_logger.event_end('export_csv')
    return response

@bp.route('/export.xlsx', methods=['GET'])
@require_admin
def export_xlsx():
    """Export assessment results to Excel with optional filters."""
    export_logger.event_start('export_xlsx')
    
    frente = request.args.get('frente')
    department = request.args.get('department')
    role = request.args.get('role')
    
    export_logger.event_info('export_xlsx', {'frente': frente, 'department': department, 'role': role})
    
    filepath = export_to_xlsx(frente=frente, department=department, role=role)
    
    filter_parts = []
    if frente:
        filter_parts.append(frente.lower())
    if department:
        filter_parts.append(department.lower().replace(' ', '_'))
    if role:
        filter_parts.append(role.lower().replace(' ', '_'))
    
    filename = 'oaz_profiler'
    if filter_parts:
        filename += '_' + '_'.join(filter_parts)
    filename += '.xlsx'
    
    log_audit(
        actor=flask_session.get('admin_username', 'admin'),
        action='export_xlsx',
        target='data',
        payload={'frente': frente, 'department': department, 'role': role}
    )
    
    export_logger.event_success('export_xlsx', {'filename': filename})
    export_logger.event_end('export_xlsx')
    return send_file(filepath, as_attachment=True, download_name=filename)

@bp.route('/stats/global', methods=['GET'])
@require_admin
def stats_global():
    """Get global OAZ statistics."""
    admin_logger.event_start('stats_global_load')
    result = get_global_stats()
    admin_logger.event_success('stats_global_load')
    admin_logger.event_end('stats_global_load')
    return jsonify(result)

@bp.route('/stats/frentes', methods=['GET'])
@require_admin
def stats_frentes():
    """Get statistics by frente (SOUQ, THESAINT)."""
    admin_logger.event_start('stats_frentes_load')
    result = get_frente_stats()
    admin_logger.event_success('stats_frentes_load')
    admin_logger.event_end('stats_frentes_load')
    return jsonify(result)

@bp.route('/stats/departments', methods=['GET'])
@require_admin
def stats_departments():
    """Get statistics by department."""
    admin_logger.event_start('stats_departments_load')
    result = get_department_stats()
    admin_logger.event_success('stats_departments_load')
    admin_logger.event_end('stats_departments_load')
    return jsonify(result)

@bp.route('/stats/roles', methods=['GET'])
@require_admin
def stats_roles():
    """Get statistics by role/cargo."""
    admin_logger.event_start('stats_roles_load')
    result = get_role_stats()
    admin_logger.event_success('stats_roles_load')
    admin_logger.event_end('stats_roles_load')
    return jsonify(result)

@bp.route('/stats/all', methods=['GET'])
@require_admin
def stats_all():
    """Get complete dashboard statistics."""
    admin_logger.event_start('stats_all_load')
    result = get_complete_dashboard_data()
    admin_logger.event_success('stats_all_load')
    admin_logger.event_end('stats_all_load')
    return jsonify(result)

@bp.route('/frontend-log', methods=['POST'])
def frontend_log():
    """Receive logs from frontend JavaScript."""
    from app.services.logger import get_logger
    frontend_logger = get_logger('frontend')
    
    data = request.get_json()
    event_type = data.get('type', 'info')
    action = data.get('action', 'unknown')
    details = data.get('details', {})
    
    if event_type == 'click':
        frontend_logger.event_info(f"user_click_{action}", details)
    elif event_type == 'tab':
        frontend_logger.event_info(f"tab_switch_{action}", details)
    elif event_type == 'form':
        frontend_logger.event_info(f"form_submit_{action}", details)
    elif event_type == 'page':
        frontend_logger.event_info(f"page_view_{action}", details)
    elif event_type == 'error':
        frontend_logger.event_error(f"frontend_error_{action}", details=details)
    else:
        frontend_logger.event_info(f"frontend_{action}", details)
    
    return jsonify({'status': 'logged'})
