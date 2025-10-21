from flask import Blueprint, request, jsonify, session as flask_session
from app.models import Session
from app.agents.orchestrator import AgentOrchestrator
from app.core.security import sanitize_input

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
    """Submit response to current item."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        return jsonify({'error': 'Sessão inválida'}), 400
    
    data = request.get_json()
    item_id = data.get('item_id')
    answer = sanitize_input(data.get('answer', ''))
    latency_ms = data.get('latency_ms')
    
    if not item_id or not answer:
        return jsonify({'error': 'Item ID e resposta são obrigatórios'}), 400
    
    orchestrator = AgentOrchestrator(session_id)
    
    result = orchestrator.process_response(item_id, answer, latency_ms)
    
    stop_check = orchestrator.should_stop()
    
    return jsonify({
        'success': True,
        'score': result['score'],
        'items_answered': result['items_answered'],
        'should_stop': stop_check['should_stop'],
        'stop_reason': stop_check['reason'],
        'message': 'Resposta processada com sucesso'
    })
