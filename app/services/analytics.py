from app.models import User, Session, ProficiencySnapshot
from app import db
from sqlalchemy import func
from collections import defaultdict

FRENTE_MAPPING = {
    'oaz.co': 'SOUQ',
    'thesaint.com.br': 'THESAINT'
}

def get_frente_from_email(email):
    if not email:
        return None
    domain = email.split('@')[-1].lower()
    return FRENTE_MAPPING.get(domain, 'Outro')

def get_user_latest_snapshot(user_id):
    session = Session.query.filter_by(
        user_id=user_id,
        status='completed'
    ).order_by(Session.ended_at.desc()).first()
    
    if not session:
        return None
    
    return ProficiencySnapshot.query.filter_by(session_id=session.id).first()

def get_all_completed_snapshots():
    completed_sessions = Session.query.filter_by(status='completed').subquery()
    
    snapshots = db.session.query(
        ProficiencySnapshot,
        User
    ).join(
        completed_sessions,
        ProficiencySnapshot.session_id == completed_sessions.c.id
    ).join(
        User,
        completed_sessions.c.user_id == User.id
    ).all()
    
    return snapshots

def compute_aggregated_stats(snapshots_with_users):
    if not snapshots_with_users:
        return {
            'count': 0,
            'avg_score': 0,
            'level_distribution': {
                'Iniciante': 0,
                'Explorador': 0,
                'Praticante': 0,
                'Líder Digital': 0
            },
            'block_averages': {}
        }
    
    scores = []
    level_distribution = defaultdict(int)
    block_scores_sum = defaultdict(list)
    
    for snapshot, user in snapshots_with_users:
        if snapshot.raw_score is not None:
            scores.append(snapshot.raw_score)
        
        if snapshot.maturity_level:
            level_distribution[snapshot.maturity_level] += 1
        
        if snapshot.block_scores:
            for block, score in snapshot.block_scores.items():
                block_scores_sum[block].append(score)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    block_averages = {}
    for block, scores_list in block_scores_sum.items():
        block_averages[block] = round(sum(scores_list) / len(scores_list), 1) if scores_list else 0
    
    level_dist = {
        'Iniciante': level_distribution.get('Iniciante', 0),
        'Explorador': level_distribution.get('Explorador', 0),
        'Praticante': level_distribution.get('Praticante', 0),
        'Líder Digital': level_distribution.get('Líder Digital', 0)
    }
    
    return {
        'count': len(snapshots_with_users),
        'avg_score': round(avg_score, 1),
        'level_distribution': level_dist,
        'block_averages': block_averages
    }

def get_global_stats():
    snapshots = get_all_completed_snapshots()
    stats = compute_aggregated_stats(snapshots)
    stats['label'] = 'OAZ Global'
    return stats

def get_frente_stats():
    snapshots = get_all_completed_snapshots()
    
    frentes = defaultdict(list)
    for snapshot, user in snapshots:
        frente = get_frente_from_email(user.email)
        frentes[frente].append((snapshot, user))
    
    result = {}
    for frente, frente_snapshots in frentes.items():
        stats = compute_aggregated_stats(frente_snapshots)
        stats['label'] = frente
        result[frente] = stats
    
    return result

def get_department_stats():
    snapshots = get_all_completed_snapshots()
    
    departments = defaultdict(list)
    for snapshot, user in snapshots:
        dept = user.department if user.department else 'Não informado'
        departments[dept].append((snapshot, user))
    
    result = {}
    for dept, dept_snapshots in departments.items():
        stats = compute_aggregated_stats(dept_snapshots)
        stats['label'] = dept
        result[dept] = stats
    
    return result

def get_role_stats():
    snapshots = get_all_completed_snapshots()
    
    roles = defaultdict(list)
    for snapshot, user in snapshots:
        role = user.role if user.role else 'Não informado'
        roles[role].append((snapshot, user))
    
    result = {}
    for role, role_snapshots in roles.items():
        stats = compute_aggregated_stats(role_snapshots)
        stats['label'] = role
        result[role] = stats
    
    return result

def get_complete_dashboard_data():
    return {
        'global': get_global_stats(),
        'frentes': get_frente_stats(),
        'departments': get_department_stats(),
        'roles': get_role_stats()
    }
