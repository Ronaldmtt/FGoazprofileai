import csv
import pandas as pd
from app.models import User, Session, ProficiencySnapshot
from app.core.scoring import IRTScorer
from datetime import datetime
import os

def export_to_csv() -> str:
    """Export assessment results to CSV file."""
    rows = []
    
    users = User.query.all()
    irt = IRTScorer()
    
    for user in users:
        sessions = Session.query.filter_by(user_id=user.id, status='completed').all()
        
        for session in sessions:
            snapshots = ProficiencySnapshot.query.filter_by(session_id=session.id).all()
            
            if not snapshots:
                continue
            
            scores = {s.competency: s.score_0_100 for s in snapshots}
            global_score = irt.calculate_global_score(scores)
            global_level = irt.calculate_level(global_score)
            
            row = {
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
                'department': user.department,
                'role': user.role,
                'session_id': session.id,
                'started_at': session.started_at.isoformat(),
                'ended_at': session.ended_at.isoformat() if session.ended_at else '',
                'time_spent_s': session.time_spent_s,
                'global_score': round(global_score, 1),
                'global_level': global_level
            }
            
            for snapshot in snapshots:
                row[f'score_{snapshot.competency}'] = round(snapshot.score_0_100, 1)
            
            rows.append(row)
    
    filepath = '/tmp/oaz_profiler_export.csv'
    
    if rows:
        fieldnames = list(rows[0].keys())
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['No data available'])
    
    return filepath

def export_to_xlsx() -> str:
    """Export assessment results to Excel file."""
    users = User.query.all()
    irt = IRTScorer()
    
    data = []
    
    for user in users:
        sessions = Session.query.filter_by(user_id=user.id, status='completed').all()
        
        for session in sessions:
            snapshots = ProficiencySnapshot.query.filter_by(session_id=session.id).all()
            
            if not snapshots:
                continue
            
            scores = {s.competency: s.score_0_100 for s in snapshots}
            global_score = irt.calculate_global_score(scores)
            global_level = irt.calculate_level(global_score)
            
            row = {
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
                'department': user.department,
                'role': user.role,
                'session_id': session.id,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'time_spent_s': session.time_spent_s,
                'global_score': round(global_score, 1),
                'global_level': global_level
            }
            
            for snapshot in snapshots:
                row[f'{snapshot.competency}'] = round(snapshot.score_0_100, 1)
            
            data.append(row)
    
    filepath = '/tmp/oaz_profiler_export.xlsx'
    
    if data:
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
    else:
        df = pd.DataFrame({'message': ['No data available']})
        df.to_excel(filepath, index=False, engine='openpyxl')
    
    return filepath
