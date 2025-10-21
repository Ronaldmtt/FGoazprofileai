from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session as flask_session
from app.models import Session, User
from app.agents.orchestrator import AgentOrchestrator
from app.core.security import sanitize_input
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
    user_id = flask_session.get('user_id')
    user = User.query.get(user_id)
    
    active_session = Session.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if active_session:
        return redirect(url_for('items.next_page'))
    
    return render_template('start.html', user=user)

@bp.route('/start', methods=['POST'])
@require_auth
def start():
    """Start new assessment session with P0 response."""
    user_id = flask_session.get('user_id')
    
    active_session = Session.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if active_session:
        return jsonify({'error': 'Já existe uma sessão ativa'}), 400
    
    data = request.get_json()
    initial_response = sanitize_input(data.get('initial_response', ''))
    
    if not initial_response or len(initial_response) < 5:
        return jsonify({'error': 'Por favor, forneça uma resposta inicial'}), 400
    
    session = Session(
        user_id=user_id,
        initial_response=initial_response,
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    
    flask_session['session_id'] = session.id
    
    return jsonify({
        'session_id': session.id,
        'message': 'Sessão iniciada com sucesso',
        'redirect': url_for('items.next_page')
    })

@bp.route('/finish', methods=['POST'])
@require_auth
def finish():
    """Finish current session and generate recommendations."""
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Nenhuma sessão ativa'}), 400
    
    session = Session.query.get(session_id)
    
    if not session or session.status != 'active':
        return jsonify({'error': 'Sessão inválida'}), 400
    
    orchestrator = AgentOrchestrator(session_id)
    
    recommendations_data = orchestrator.generate_recommendations()
    
    from app.agents.scorer import AgentScorer
    from app.models import Recommendation
    
    scorer = AgentScorer()
    scorer.save_snapshot(session_id, orchestrator.state['proficiency'])
    
    recommendation = Recommendation(
        user_id=session.user_id,
        session_id=session_id
    )
    recommendation.tracks = recommendations_data['tracks']
    db.session.add(recommendation)
    
    session.status = 'completed'
    session.ended_at = datetime.utcnow()
    session.time_spent_s = int((session.ended_at - session.started_at).total_seconds())
    db.session.commit()
    
    flask_session.pop('session_id', None)
    
    return jsonify({
        'message': 'Avaliação concluída!',
        'redirect': url_for('session.result')
    })

@bp.route('/result', methods=['GET'])
@require_auth
def result():
    """Show assessment results to user."""
    user_id = flask_session.get('user_id')
    
    session = Session.query.filter_by(
        user_id=user_id,
        status='completed'
    ).order_by(Session.ended_at.desc()).first()
    
    if not session:
        return render_template('error.html',
            message='Nenhuma avaliação concluída encontrada.')
    
    from app.models import ProficiencySnapshot, Recommendation
    from app.core.scoring import IRTScorer
    
    snapshots = ProficiencySnapshot.query.filter_by(session_id=session.id).all()
    recommendation = Recommendation.query.filter_by(session_id=session.id).first()
    
    proficiency_data = {s.competency: s.score_0_100 for s in snapshots}
    
    irt = IRTScorer()
    global_score = irt.calculate_global_score(proficiency_data)
    global_level = irt.calculate_level(global_score)
    
    return render_template('result.html',
        session=session,
        snapshots=snapshots,
        global_score=global_score,
        global_level=global_level,
        recommendation=recommendation,
        irt=irt
    )
