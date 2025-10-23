from app import db

class ProficiencySnapshot(db.Model):
    __tablename__ = 'proficiency_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    
    # NEW: Support both block (matrix) and competency (legacy IRT)
    block = db.Column(db.String(100), index=True)  # NEW: for matrix assessment
    competency = db.Column(db.String(100), index=True)  # Legacy: for IRT assessment
    
    # Scores
    score_0_100 = db.Column(db.Float, nullable=False)  # Universal score (0-100)
    raw_points = db.Column(db.Integer)  # NEW: Raw points for matrix (e.g., 1-4 per question)
    max_points = db.Column(db.Integer)  # NEW: Maximum possible points
    
    # Confidence intervals (only for IRT legacy)
    ci_low = db.Column(db.Float)
    ci_high = db.Column(db.Float)
    
    session = db.relationship('Session', back_populates='snapshots')
    
    def get_block_or_competency(self):
        """Returns block (new system) or competency (legacy)."""
        return self.block if self.block else self.competency
    
    def __repr__(self):
        identifier = self.block if self.block else self.competency
        return f'<ProficiencySnapshot {identifier}: {self.score_0_100}>'
