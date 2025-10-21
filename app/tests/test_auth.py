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
    """Test magic link generation with valid @oaz.co email."""
    response = client.post('/auth/magic-link', json={
        'email': 'test@oaz.co'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'dev_link' in data

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
    from app.core.security import generate_token
    
    with app.app_context():
        token = generate_token('newuser@oaz.co')
    
    response = client.get(f'/auth/verify?token={token}')
    assert response.status_code == 302
    assert '/auth/consent' in response.location

def test_user_creation_with_consent(client, app):
    """Test user creation when consent is provided."""
    from app.core.security import generate_token
    
    with app.app_context():
        token = generate_token('newuser@oaz.co')
    
    response = client.post(f'/auth/consent?token={token}', data={
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
