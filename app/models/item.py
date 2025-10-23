from app import db
import json

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    stem = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    
    # NEW: Block-based system (Matriz de 4 Blocos)
    # Use 'block' for new matrix questions, 'competency' for legacy
    block = db.Column(db.String(100), index=True)  # One of 4 blocks
    competency = db.Column(db.String(100), index=True)  # Legacy field (will be deprecated)
    
    # IRT parameters (only for legacy adaptive questions)
    difficulty_b = db.Column(db.Float, default=1.0)
    discrimination_a = db.Column(db.Float, default=0.5)
    
    # Question content
    choices_json = db.Column(db.Text)
    answer_key = db.Column(db.String(10))  # Legacy: for MCQ with single correct answer
    rubric_json = db.Column(db.Text)
    
    # Metadata
    progressive_levels = db.Column(db.Boolean, default=False)  # NEW: True for matrix questions (A=1, B=2, C=3, D=4)
    metadata_json = db.Column(db.Text)  # Additional data
    tags = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True, index=True)
    
    responses = db.relationship('Response', back_populates='item', lazy='dynamic')
    
    @property
    def choices(self):
        if self.choices_json:
            return json.loads(self.choices_json)
        return []
    
    @choices.setter
    def choices(self, value):
        self.choices_json = json.dumps(value, ensure_ascii=False)
    
    @property
    def rubric(self):
        if self.rubric_json:
            return json.loads(self.rubric_json)
        return {}
    
    @rubric.setter
    def rubric(self, value):
        self.rubric_json = json.dumps(value, ensure_ascii=False)
    
    def get_metadata(self):
        """Get metadata dict from JSON field."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
    
    def set_metadata(self, value):
        """Set metadata from dict to JSON field."""
        self.metadata_json = json.dumps(value, ensure_ascii=False)
    
    def get_block_or_competency(self):
        """Returns block (new system) or competency (legacy)."""
        return self.block if self.block else self.competency
    
    def is_matrix_question(self):
        """Check if this is a matrix question (progressive levels)."""
        return self.progressive_levels == True or self.type == 'matrix'
    
    def __repr__(self):
        identifier = self.block if self.block else self.competency
        return f'<Item {self.id} - {self.type} - {identifier}>'
