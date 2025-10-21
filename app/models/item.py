from app import db
import json

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    stem = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    competency = db.Column(db.String(100), nullable=False, index=True)
    difficulty_b = db.Column(db.Float, default=1.0)
    discrimination_a = db.Column(db.Float, default=0.5)
    choices_json = db.Column(db.Text)
    answer_key = db.Column(db.String(10))
    rubric_json = db.Column(db.Text)
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
    
    def __repr__(self):
        return f'<Item {self.id} - {self.type}>'
