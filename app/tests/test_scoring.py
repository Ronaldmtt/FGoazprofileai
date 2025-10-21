import pytest
from app.core.scoring import IRTScorer
from app.agents.grader import AgentGrader
from app.agents.scorer import AgentScorer
from app import create_app, db
from app.models import Item, Session, User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SEED_ON_START = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_irt_scorer_update_proficiency():
    """Test IRT scoring updates proficiency correctly."""
    scorer = IRTScorer()
    
    new_score, new_ci = scorer.update_proficiency(
        current_score=50.0,
        current_ci=30.0,
        item_difficulty=2.0,
        item_discrimination=0.8,
        response_score=1.0
    )
    
    assert new_score > 50.0
    assert new_ci < 30.0

def test_irt_scorer_calculate_level():
    """Test level calculation based on score."""
    scorer = IRTScorer()
    
    assert scorer.calculate_level(25) == 'N0'
    assert scorer.calculate_level(35) == 'N1'
    assert scorer.calculate_level(55) == 'N2'
    assert scorer.calculate_level(70) == 'N3'
    assert scorer.calculate_level(85) == 'N4'
    assert scorer.calculate_level(95) == 'N5'

def test_grader_mcq_correct(app):
    """Test MCQ grading for correct answer."""
    with app.app_context():
        item = Item(
            stem='Test question',
            type='mcq',
            competency='Test',
            answer_key='A'
        )
        db.session.add(item)
        db.session.commit()
        
        grader = AgentGrader()
        result = grader.grade_response(item, 'A')
        
        assert result['score'] == 1.0
        assert result['breakdown']['correct'] is True

def test_grader_mcq_incorrect(app):
    """Test MCQ grading for incorrect answer."""
    with app.app_context():
        item = Item(
            stem='Test question',
            type='mcq',
            competency='Test',
            answer_key='A'
        )
        db.session.add(item)
        db.session.commit()
        
        grader = AgentGrader()
        result = grader.grade_response(item, 'B')
        
        assert result['score'] == 0.0
        assert result['breakdown']['correct'] is False

def test_grader_open_ended(app):
    """Test open-ended response grading."""
    with app.app_context():
        item = Item(
            stem='Explain AI',
            type='open_ended',
            competency='Test'
        )
        item.rubric = {
            'relevancia': 'Mentions AI concepts',
            'precisao': 'Accurate information'
        }
        db.session.add(item)
        db.session.commit()
        
        grader = AgentGrader()
        result = grader.grade_response(
            item,
            'Inteligência Artificial é a capacidade de sistemas computacionais realizarem tarefas que normalmente requerem inteligência humana, como reconhecimento de padrões, tomada de decisões e processamento de linguagem natural.'
        )
        
        assert 'score' in result
        assert result['score'] > 0
        assert 'breakdown' in result

def test_proficiency_convergence(app):
    """Test that proficiency converges with multiple responses."""
    with app.app_context():
        user = User(email='test@oaz.co', consent_ts=db.func.current_timestamp())
        db.session.add(user)
        db.session.commit()
        
        session = Session(user_id=user.id, initial_response='Test', status='active')
        db.session.add(session)
        db.session.commit()
        
        item = Item(
            stem='Test',
            type='mcq',
            competency='Fundamentos de IA/ML & LLMs',
            difficulty_b=1.0,
            discrimination_a=0.7,
            answer_key='A'
        )
        db.session.add(item)
        db.session.commit()
        
        scorer = AgentScorer()
        proficiency = {
            'Fundamentos de IA/ML & LLMs': {
                'score': 50.0,
                'ci_low': 20.0,
                'ci_high': 80.0,
                'items_count': 0
            }
        }
        
        updated = scorer.update_proficiency(
            session.id,
            item,
            1.0,
            proficiency
        )
        
        assert updated['Fundamentos de IA/ML & LLMs']['score'] != 50.0
        ci_width = updated['Fundamentos de IA/ML & LLMs']['ci_high'] - updated['Fundamentos de IA/ML & LLMs']['ci_low']
        original_ci_width = 80.0 - 20.0
        assert ci_width < original_ci_width
