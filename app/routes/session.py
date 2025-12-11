from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session
from app.models import Session, User
from app.agents.orchestrator_matrix import AgentOrchestratorMatrix
from app.core.security import sanitize_input
from app.services.logger import assessment_logger
from app import db
from datetime import datetime

bp = Blueprint('session', __name__, url_prefix='/session')

def require_auth(f):
    """Decorator to require authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in flask_session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/start', methods=['GET'])
@require_auth
def start_page():
    """Render session start page with P0 question."""
    assessment_logger.event_start('assessment_start_page_load')
    user_id = flask_session.get('user_id')
    user = User.query.get(user_id)
    
    assessment_logger.event_info('assessment_start_page_load', {'user_id': user_id})
    
    active_session = Session.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if active_session:
        flask_session['session_id'] = active_session.id
        assessment_logger.event_info('assessment_start_page_load', {'action': 'redirect_to_active_session', 'session_id': active_session.id})
        assessment_logger.event_end('assessment_start_page_load')
        return redirect(url_for('items.next_page'))
    
    assessment_logger.event_success('assessment_start_page_load')
    assessment_logger.event_end('assessment_start_page_load')
    return render_template('start.html', user=user)

@bp.route('/start', methods=['POST'])
@require_auth
def start():
    """Start new assessment session with P0 response."""
    assessment_logger.event_start('assessment_session_create')
    user_id = flask_session.get('user_id')
    
    assessment_logger.event_info('assessment_session_create', {'user_id': user_id})
    
    active_session = Session.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if active_session:
        assessment_logger.event_error('assessment_session_create', details={'reason': 'session_already_active', 'session_id': active_session.id})
        assessment_logger.event_end('assessment_session_create')
        return jsonify({'error': 'Já existe uma sessão ativa'}), 400
    
    data = request.get_json()
    initial_response = sanitize_input(data.get('initial_response', ''))
    
    if not initial_response or len(initial_response) < 5:
        assessment_logger.event_error('assessment_session_create', details={'reason': 'invalid_initial_response'})
        assessment_logger.event_end('assessment_session_create')
        return jsonify({'error': 'Por favor, forneça uma resposta inicial'}), 400
    
    session = Session()
    session.user_id = user_id
    session.initial_response = initial_response
    session.status = 'active'
    
    db.session.add(session)
    db.session.commit()
    
    flask_session['session_id'] = session.id
    
    assessment_logger.event_success('assessment_session_create', {'session_id': session.id, 'user_id': user_id})
    assessment_logger.event_end('assessment_session_create')
    
    return jsonify({
        'session_id': session.id,
        'message': 'Sessão iniciada com sucesso',
        'redirect': url_for('items.next_page')
    })

@bp.route('/finish', methods=['POST'])
@require_auth
def finish():
    """Finish current session and save final results."""
    assessment_logger.event_start('assessment_finish')
    session_id = flask_session.get('session_id')
    
    if not session_id:
        assessment_logger.event_error('assessment_finish', details={'reason': 'no_active_session'})
        assessment_logger.event_end('assessment_finish')
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    assessment_logger.event_info('assessment_finish', {'session_id': session_id})
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        assessment_logger.event_error('assessment_finish', details={'reason': 'invalid_session', 'session_id': session_id})
        assessment_logger.event_end('assessment_finish')
        return jsonify({'error': 'Sessão inválida'}), 400
    
    assessment_logger.event_info('assessment_finish', {'action': 'calling_orchestrator_finalize'})
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    final_results = orchestrator.finalize_assessment()
    
    db.session.refresh(session)
    
    session.ended_at = datetime.utcnow()
    session.time_spent_s = int((session.ended_at - session.started_at).total_seconds())
    db.session.commit()
    
    flask_session.pop('session_id', None)
    
    assessment_logger.event_success('assessment_finish', {
        'session_id': session_id,
        'time_spent_s': session.time_spent_s,
        'raw_score': final_results.get('raw_score'),
        'maturity_level': final_results.get('maturity_level')
    })
    assessment_logger.event_end('assessment_finish')
    
    return jsonify({
        'message': 'Avaliação concluída!',
        'redirect': url_for('session.result'),
        'results': final_results
    })

@bp.route('/result', methods=['GET'])
@require_auth
def result():
    """Show assessment results to user (matrix-based)."""
    assessment_logger.event_start('assessment_result_view')
    user_id = flask_session.get('user_id')
    
    assessment_logger.event_info('assessment_result_view', {'user_id': user_id})
    
    session = Session.query.filter_by(
        user_id=user_id,
        status='completed'
    ).order_by(Session.ended_at.desc()).first()
    
    if not session:
        assessment_logger.event_error('assessment_result_view', details={'reason': 'no_completed_session'})
        assessment_logger.event_end('assessment_result_view')
        return render_template('error.html',
            message='Nenhuma avaliação concluída encontrada.')
    
    from app.models import ProficiencySnapshot
    
    snapshot = ProficiencySnapshot.query.filter_by(session_id=session.id).first()
    
    if not snapshot:
        assessment_logger.event_error('assessment_result_view', details={'reason': 'no_snapshot', 'session_id': session.id})
        assessment_logger.event_end('assessment_result_view')
        return render_template('error.html',
            message='Resultados não encontrados para esta avaliação.')
    
    assessment_logger.event_success('assessment_result_view', {
        'session_id': session.id,
        'raw_score': snapshot.raw_score,
        'maturity_level': snapshot.maturity_level
    })
    assessment_logger.event_end('assessment_result_view')
    
    return render_template('result_matrix.html',
        assessment_session=session,
        snapshot=snapshot,
        total_score=snapshot.raw_score,
        maturity_level=snapshot.maturity_level,
        block_scores=snapshot.block_scores
    )
