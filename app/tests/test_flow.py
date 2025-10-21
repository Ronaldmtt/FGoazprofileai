import pytest
from app import create_app, db
from app.models import User, Session, Item, Response
from app.core.utils import seed_database
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    SEED_ON_START = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        
        user = User(
            email='test@oaz.co',
            name='Test User',
            consent_ts=db.func.current_timestamp()
        )
        db.session.add(user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client, app):
    """Client with authenticated session."""
    with client.session_transaction() as sess:
        with app.app_context():
            user = User.query.filter_by(email='test@oaz.co').first()
            sess['user_id'] = user.id
            sess['email'] = user.email
    return client

def test_session_start_requires_auth(client):
    """Test that session start requires authentication."""
    response = client.get('/session/start')
    assert response.status_code == 302

def test_session_start_flow(authenticated_client, app):
    """Test complete session start flow."""
    response = authenticated_client.post('/session/start', json={
        'initial_response': 'Eu usaria IA para automatizar relatórios e análises de dados.'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'session_id' in data
    
    with app.app_context():
        session = Session.query.get(data['session_id'])
        assert session is not None
        assert session.status == 'active'
        assert session.initial_response is not None

def test_item_response_submission(authenticated_client, app):
    """Test submitting responses to items."""
    with app.app_context():
        user = User.query.filter_by(email='test@oaz.co').first()
        session = Session(user_id=user.id, initial_response='Test', status='active')
        db.session.add(session)
        db.session.commit()
        session_id = session.id
    
    with authenticated_client.session_transaction() as sess:
        sess['session_id'] = session_id
    
    with app.app_context():
        item = Item.query.first()
        item_id = item.id
    
    response = authenticated_client.post('/responses/', json={
        'item_id': item_id,
        'answer': 'A',
        'latency_ms': 5000
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'score' in data
    
    with app.app_context():
        response_obj = Response.query.filter_by(session_id=session_id).first()
        assert response_obj is not None

def test_session_finish(authenticated_client, app):
    """Test finishing a session."""
    with app.app_context():
        user = User.query.filter_by(email='test@oaz.co').first()
        session = Session(user_id=user.id, initial_response='Test', status='active')
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        items = Item.query.limit(3).all()
        for item in items:
            response = Response(
                session_id=session_id,
                item_id=item.id,
                raw_answer='A',
                graded_score_0_1=0.8
            )
            db.session.add(response)
        db.session.commit()
    
    with authenticated_client.session_transaction() as sess:
        sess['session_id'] = session_id
    
    response = authenticated_client.post('/session/finish')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'redirect' in data
    
    with app.app_context():
        session = Session.query.get(session_id)
        assert session.status == 'completed'
        assert session.ended_at is not None
