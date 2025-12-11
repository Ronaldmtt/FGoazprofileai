from flask import Blueprint, request, jsonify, session as flask_session
from app.models import Session
from app.agents.orchestrator_matrix import AgentOrchestratorMatrix
from app.core.security import sanitize_input
from app.services.logger import assessment_logger

bp = Blueprint('responses', __name__, url_prefix='/responses')

def require_auth(f):
    """Decorator to require authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in flask_session:
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/', methods=['POST'])
@require_auth
def submit():
    """Submit response to current item (matrix-based)."""
    assessment_logger.event_start('response_submit')
    session_id = flask_session.get('session_id')
    
    if not session_id:
        assessment_logger.event_error('response_submit', details={'reason': 'no_session'})
        assessment_logger.event_end('response_submit')
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        assessment_logger.event_error('response_submit', details={'reason': 'invalid_session', 'session_id': session_id})
        assessment_logger.event_end('response_submit')
        return jsonify({'error': 'Sessão inválida'}), 400
    
    data = request.get_json()
    item_id = data.get('item_id')
    answer = sanitize_input(data.get('answer', ''))
    latency_ms = data.get('latency_ms')
    
    assessment_logger.event_info('response_submit', {
        'session_id': session_id,
        'item_id': item_id,
        'answer': answer,
        'latency_ms': latency_ms
    })
    
    if not item_id or not answer:
        assessment_logger.event_error('response_submit', details={'reason': 'missing_data'})
        assessment_logger.event_end('response_submit')
        return jsonify({'error': 'Item ID e resposta são obrigatórios'}), 400
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    
    assessment_logger.event_info('response_submit', {'action': 'processing_response'})
    result = orchestrator.process_response(item_id, answer, latency_ms)
    
    stop_check = orchestrator.should_stop()
    
    assessment_logger.event_success('response_submit', {
        'session_id': session_id,
        'item_id': item_id,
        'points': result['points'],
        'total_score': result['total_score'],
        'items_answered': result['items_answered'],
        'should_stop': stop_check['should_stop']
    })
    assessment_logger.event_end('response_submit')
    
    return jsonify({
        'success': True,
        'points': result['points'],
        'total_score': result['total_score'],
        'items_answered': result['items_answered'],
        'should_stop': stop_check['should_stop'],
        'stop_reason': stop_check['reason'],
        'message': 'Resposta processada com sucesso'
    })
