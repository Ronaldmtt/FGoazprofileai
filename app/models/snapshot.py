from app import db
import json

class ProficiencySnapshot(db.Model):
    __tablename__ = 'proficiency_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    
    # NEW: Support both block (matrix) and competency (legacy IRT)
    block = db.Column(db.String(100), index=True)  # NEW: for matrix assessment
    competency = db.Column(db.String(100), index=True)  # Legacy: for IRT assessment
    
    # Scores
    score_0_100 = db.Column(db.Float)  # Universal score (0-100), legacy
    raw_score = db.Column(db.Integer)  # NEW: Total raw score (10-40 for matrix)
    raw_points = db.Column(db.Integer)  # Legacy: Raw points per competency
    max_points = db.Column(db.Integer)  # Maximum possible points
    
    # Matrix-specific fields
    maturity_level = db.Column(db.String(50))  # Iniciante, Explorador, Praticante, Líder Digital
    block_scores_json = db.Column(db.Text)  # JSON: scores per block
    
    # Confidence intervals (only for IRT legacy)
    ci_low = db.Column(db.Float)
    ci_high = db.Column(db.Float)
    
    session = db.relationship('Session', back_populates='snapshots')
    
    @property
    def block_scores(self):
        """Get block scores from JSON."""
        if self.block_scores_json:
            return json.loads(self.block_scores_json)
        return {}
    
    @block_scores.setter
    def block_scores(self, value):
        """Set block scores to JSON."""
        self.block_scores_json = json.dumps(value, ensure_ascii=False)
    
    def get_block_or_competency(self):
        """Returns block (new system) or competency (legacy)."""
        return self.block if self.block else self.competency
    
    def __repr__(self):
        identifier = self.block if self.block else self.competency
        return f'<ProficiencySnapshot {identifier}: {self.score_0_100}>'
