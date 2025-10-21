from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session
from app.models import Item, Session
from app.agents.orchestrator import AgentOrchestrator

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
    """Render next item page."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return redirect(url_for('session.start_page'))
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        return redirect(url_for('session.start_page'))
    
    orchestrator = AgentOrchestrator(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        return redirect(url_for('session.finish_page'))
    
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        # If OpenAI generation failed, show error
        return render_template('error.html',
            message="Não foi possível gerar a próxima pergunta personalizada. Verifique se a chave da OpenAI está configurada corretamente."
        )
    
    progress = {
        'current': orchestrator.state['items_answered'] + 1,
        'total': 12,
        'percentage': int((orchestrator.state['items_answered'] / 12) * 100)
    }
    
    return render_template('item.html',
        item=next_item,
        progress=progress
    )

@bp.route('/next', methods=['POST'])
@require_auth
def next_api():
    """API endpoint to get next item (for HTMX)."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    orchestrator = AgentOrchestrator(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        return jsonify({
            'should_stop': True,
            'reason': stop_check['reason'],
            'redirect': url_for('session.finish_page')
        })
    
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        return jsonify({
            'error': True,
            'message': 'Falha na geração de pergunta personalizada pela OpenAI. Verifique a configuração da API key.'
        }), 500
    
    return jsonify({
        'item_id': next_item.id,
        'stem': next_item.stem,
        'type': next_item.type,
        'choices': next_item.choices if next_item.type in ['mcq', 'scenario'] else None,
        'progress': {
            'current': orchestrator.state['items_answered'] + 1,
            'total': 12
        }
    })

@bp.route('/finish-page', methods=['GET'])
@require_auth
def finish_page():
    """Render finish page before final submission."""
    return render_template('finish.html')
