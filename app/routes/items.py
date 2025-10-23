from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session
from app.models import Item, Session
from app.agents.orchestrator_matrix import AgentOrchestratorMatrix
from app.core.blocks_config import TOTAL_QUESTIONS

bp = Blueprint('items', __name__, url_prefix='/items')

def require_auth(f):
    """Decorator to require authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in flask_session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/next', methods=['GET'])
@require_auth
def next_page():
    """Render next item page (matrix-based)."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return redirect(url_for('session.start_page'))
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        return redirect(url_for('session.start_page'))
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        return redirect(url_for('items.finish_page'))
    
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        return render_template('error.html',
            message="Não foi possível gerar a próxima pergunta. Verifique se a chave da OpenAI está configurada corretamente."
        )
    
    progress_info = orchestrator.get_progress()
    progress = {
        'current': orchestrator.state['items_answered'] + 1,
        'total': TOTAL_QUESTIONS,
        'percentage': int(progress_info['progress_percentage'])
    }
    
    return render_template('item.html',
        item=next_item,
        progress=progress
    )

@bp.route('/next', methods=['POST'])
@require_auth
def next_api():
    """API endpoint to get next item (for HTMX) - matrix-based."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        return jsonify({
            'should_stop': True,
            'reason': stop_check['reason'],
            'redirect': url_for('items.finish_page')
        })
    
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        return jsonify({
            'error': True,
            'message': 'Falha na geração de pergunta pela OpenAI. Verifique a configuração da API key.'
        }), 500
    
    return jsonify({
        'item_id': next_item.id,
        'stem': next_item.stem,
        'type': next_item.type,
        'choices': next_item.choices,
        'progress': {
            'current': orchestrator.state['items_answered'] + 1,
            'total': TOTAL_QUESTIONS
        }
    })

@bp.route('/finish-page', methods=['GET'])
@require_auth
def finish_page():
    """Render finish page before final submission."""
    return render_template('finish.html')
