from datetime import datetime
from app import db
import json

class Audit(db.Model):
    __tablename__ = 'audits'
    
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(255))
    action = db.Column(db.String(100), nullable=False, index=True)
    target = db.Column(db.String(100))
    payload_json = db.Column(db.Text)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @property
    def payload(self):
        if self.payload_json:
            return json.loads(self.payload_json)
        return {}
    
    @payload.setter
    def payload(self, value):
        self.payload_json = json.dumps(value, ensure_ascii=False)
    
    def __repr__(self):
        return f'<Audit {self.action} by {self.actor}>'
