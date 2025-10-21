from app import db

class ProficiencySnapshot(db.Model):
    __tablename__ = 'proficiency_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    competency = db.Column(db.String(100), nullable=False)
    score_0_100 = db.Column(db.Float, nullable=False)
    ci_low = db.Column(db.Float)
    ci_high = db.Column(db.Float)
    
    session = db.relationship('Session', back_populates='snapshots')
    
    def __repr__(self):
        return f'<ProficiencySnapshot {self.competency}: {self.score_0_100}>'
