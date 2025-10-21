from datetime import datetime
from app import db
import json

class Response(db.Model):
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False, index=True)
    raw_answer = db.Column(db.Text)
    graded_score_0_1 = db.Column(db.Float)
    rubric_breakdown_json = db.Column(db.Text)
    latency_ms = db.Column(db.Integer)
    ai_flags_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('Session', back_populates='responses')
    item = db.relationship('Item', back_populates='responses')
    
    @property
    def rubric_breakdown(self):
        if self.rubric_breakdown_json:
            return json.loads(self.rubric_breakdown_json)
        return {}
    
    @rubric_breakdown.setter
    def rubric_breakdown(self, value):
        self.rubric_breakdown_json = json.dumps(value, ensure_ascii=False)
    
    @property
    def ai_flags(self):
        if self.ai_flags_json:
            return json.loads(self.ai_flags_json)
        return {}
    
    @ai_flags.setter
    def ai_flags(self, value):
        self.ai_flags_json = json.dumps(value, ensure_ascii=False)
    
    def __repr__(self):
        return f'<Response {self.id}>'
