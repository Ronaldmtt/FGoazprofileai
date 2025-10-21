import pytest
from app import create_app, db
from app.models import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    ALLOWED_EMAIL_DOMAIN = 'oaz.co'
    SEED_ON_START = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_magic_link_valid_domain(client):
    """Test direct login with valid @oaz.co email (new user)."""
    response = client.post('/auth/magic-link', json={
        'email': 'test@oaz.co'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert '/auth/consent' in data['redirect']

def test_magic_link_invalid_domain(client):
    """Test magic link rejection for non-@oaz.co email."""
    response = client.post('/auth/magic-link', json={
        'email': 'test@gmail.com'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'oaz.co' in data['error']

def test_consent_required(client, app):
    """Test that consent is required for new users."""
    # Simulate login flow
    with client.session_transaction() as sess:
        sess['pending_email'] = 'newuser@oaz.co'
    
    response = client.get('/auth/consent')
    assert response.status_code == 200
    assert b'Termo de Consentimento' in response.data

def test_user_creation_with_consent(client, app):
    """Test user creation when consent is provided."""
    # Simulate login flow - set pending_email in session
    with client.session_transaction() as sess:
        sess['pending_email'] = 'newuser@oaz.co'
    
    response = client.post('/auth/consent', data={
        'consent': 'true',
        'name': 'Test User',
        'department': 'Tech',
        'role': 'Developer'
    })
    
    assert response.status_code == 302
    
    with app.app_context():
        user = User.query.filter_by(email='newuser@oaz.co').first()
        assert user is not None
        assert user.name == 'Test User'
        assert user.department == 'Tech'
        assert user.consent_ts is not None
