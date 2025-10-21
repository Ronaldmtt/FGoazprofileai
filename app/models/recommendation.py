from datetime import datetime
from app import db
import json

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    tracks_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='recommendations')
    session = db.relationship('Session', back_populates='recommendations')
    
    @property
    def tracks(self):
        if self.tracks_json:
            return json.loads(self.tracks_json)
        return []
    
    @tracks.setter
    def tracks(self, value):
        self.tracks_json = json.dumps(value, ensure_ascii=False)
    
    def __repr__(self):
        return f'<Recommendation {self.id}>'
