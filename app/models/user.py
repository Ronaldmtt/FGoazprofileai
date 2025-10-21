from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100))
    role = db.Column(db.String(100))
    consent_ts = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sessions = db.relationship('Session', back_populates='user', lazy='dynamic')
    recommendations = db.relationship('Recommendation', back_populates='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
