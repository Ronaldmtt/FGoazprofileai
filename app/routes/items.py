from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session
from app.models import Item, Session
from app.agents.orchestrator_matrix import AgentOrchestratorMatrix
from app.core.blocks_config import TOTAL_QUESTIONS
from app.services.logger import assessment_logger

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
    assessment_logger.event_start('item_next_page_load')
    session_id = flask_session.get('session_id')
    
    if not session_id:
        assessment_logger.event_info('item_next_page_load', {'action': 'redirect_no_session'})
        assessment_logger.event_end('item_next_page_load')
        return redirect(url_for('session.start_page'))
    
    assessment_logger.event_info('item_next_page_load', {'session_id': session_id})
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        assessment_logger.event_info('item_next_page_load', {'action': 'redirect_invalid_session'})
        assessment_logger.event_end('item_next_page_load')
        return redirect(url_for('session.start_page'))
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        assessment_logger.event_info('item_next_page_load', {'action': 'redirect_to_finish', 'reason': stop_check['reason']})
        assessment_logger.event_end('item_next_page_load')
        return redirect(url_for('items.finish_page'))
    
    assessment_logger.event_info('item_next_page_load', {'action': 'generating_next_item'})
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        assessment_logger.event_error('item_next_page_load', details={'reason': 'item_generation_failed'})
        assessment_logger.event_end('item_next_page_load')
        return render_template('error.html',
            message="Não foi possível gerar a próxima pergunta. Verifique se a chave da OpenAI está configurada corretamente."
        )
    
    progress_info = orchestrator.get_progress()
    progress = {
        'current': orchestrator.state['items_answered'] + 1,
        'total': TOTAL_QUESTIONS,
        'percentage': int(progress_info['progress_percentage'])
    }
    
    assessment_logger.event_success('item_next_page_load', {
        'item_id': next_item.id,
        'current_question': progress['current'],
        'total_questions': progress['total']
    })
    assessment_logger.event_end('item_next_page_load')
    
    return render_template('item.html',
        item=next_item,
        progress=progress
    )

@bp.route('/next', methods=['POST'])
@require_auth
def next_api():
    """API endpoint to get next item (for HTMX) - matrix-based."""
    assessment_logger.event_start('item_next_api')
    session_id = flask_session.get('session_id')
    
    if not session_id:
        assessment_logger.event_error('item_next_api', details={'reason': 'no_session'})
        assessment_logger.event_end('item_next_api')
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    assessment_logger.event_info('item_next_api', {'session_id': session_id})
    
    orchestrator = AgentOrchestratorMatrix(session_id)
    
    stop_check = orchestrator.should_stop()
    if stop_check['should_stop']:
        assessment_logger.event_info('item_next_api', {'action': 'should_stop', 'reason': stop_check['reason']})
        assessment_logger.event_end('item_next_api')
        return jsonify({
            'should_stop': True,
            'reason': stop_check['reason'],
            'redirect': url_for('items.finish_page')
        })
    
    assessment_logger.event_info('item_next_api', {'action': 'generating_item'})
    next_item = orchestrator.get_next_item()
    
    if not next_item:
        assessment_logger.event_error('item_next_api', details={'reason': 'generation_failed'})
        assessment_logger.event_end('item_next_api')
        return jsonify({
            'error': True,
            'message': 'Falha na geração de pergunta pela OpenAI. Verifique a configuração da API key.'
        }), 500
    
    assessment_logger.event_success('item_next_api', {
        'item_id': next_item.id,
        'current': orchestrator.state['items_answered'] + 1
    })
    assessment_logger.event_end('item_next_api')
    
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
    assessment_logger.event_start('finish_page_load')
    assessment_logger.event_success('finish_page_load')
    assessment_logger.event_end('finish_page_load')
    return render_template('finish.html')
