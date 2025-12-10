import csv
import pandas as pd
from app.models import User, Session, ProficiencySnapshot
from datetime import datetime
import os

def get_frente_from_email(email):
    """Determine frente from email domain."""
    if not email:
        return 'N/A'
    if '@oaz.co' in email.lower():
        return 'SOUQ'
    elif '@thesaint.com.br' in email.lower():
        return 'THESAINT'
    return 'Outro'

def get_export_data(frente=None, department=None, role=None):
    """Get export data with optional filters."""
    rows = []
    
    query = User.query
    users = query.all()
    
    for user in users:
        user_frente = get_frente_from_email(user.email)
        
        if frente and user_frente != frente:
            continue
        if department and user.department != department:
            continue
        if role and user.role != role:
            continue
        
        sessions = Session.query.filter_by(user_id=user.id, status='completed').all()
        
        for session in sessions:
            snapshot = ProficiencySnapshot.query.filter_by(session_id=session.id).first()
            
            if not snapshot:
                continue
            
            row = {
                'ID': user.id,
                'Nome': user.name,
                'Email': user.email,
                'Frente': user_frente,
                'Departamento': user.department or 'N/A',
                'Cargo': user.role or 'N/A',
                'Data Avaliação': session.ended_at.strftime('%d/%m/%Y %H:%M') if session.ended_at else '',
                'Tempo (min)': round(session.time_spent_s / 60, 1) if session.time_spent_s else 0,
                'Pontuação Total': snapshot.raw_score or 0,
                'Nível de Maturidade': snapshot.maturity_level or 'N/A'
            }
            
            if snapshot.block_scores:
                for block_name, score in snapshot.block_scores.items():
                    row[block_name] = score
            
            rows.append(row)
    
    return rows

def export_to_csv(frente=None, department=None, role=None) -> str:
    """Export assessment results to CSV file."""
    rows = get_export_data(frente=frente, department=department, role=role)
    
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
    
    filepath = f'/tmp/{filename}'
    
    if rows:
        fieldnames = list(rows[0].keys())
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(['Nenhum dado disponível'])
    
    return filepath

def export_to_xlsx(frente=None, department=None, role=None) -> str:
    """Export assessment results to Excel file."""
    rows = get_export_data(frente=frente, department=department, role=role)
    
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
    
    filepath = f'/tmp/{filename}'
    
    if rows:
        df = pd.DataFrame(rows)
        df.to_excel(filepath, index=False, engine='openpyxl')
    else:
        df = pd.DataFrame({'Mensagem': ['Nenhum dado disponível']})
        df.to_excel(filepath, index=False, engine='openpyxl')
    
    return filepath
