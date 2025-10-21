import pytest
from app import create_app, db
from app.models import User, Session, Item, ProficiencySnapshot
from app.core.utils import seed_database
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
        seed_database()
        
        user = User(
            email='admin@oaz.co',
            name='Admin User',
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
    """Client with authenticated admin session."""
    with client.session_transaction() as sess:
        with app.app_context():
            user = User.query.filter_by(email='admin@oaz.co').first()
            sess['user_id'] = user.id
            sess['email'] = user.email
    return client

def test_admin_overview(authenticated_client, app):
    """Test admin overview endpoint returns metrics."""
    response = authenticated_client.get('/admin/overview')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_users' in data
    assert 'total_sessions' in data
    assert 'level_distribution' in data

def test_admin_heatmap(authenticated_client, app):
    """Test competency heatmap endpoint."""
    response = authenticated_client.get('/admin/heatmap')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

def test_admin_list_items(authenticated_client, app):
    """Test listing assessment items."""
    response = authenticated_client.get('/admin/items')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_admin_create_item_valid(authenticated_client, app):
    """Test creating valid assessment item."""
    response = authenticated_client.post('/admin/items', json={
        'stem': 'What is machine learning?',
        'type': 'mcq',
        'competency': 'Fundamentos de IA/ML & LLMs',
        'difficulty_b': 1.0,
        'discrimination_a': 0.7,
        'choices': ['A', 'B', 'C', 'D'],
        'answer_key': 'A',
        'active': True
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'item_id' in data

def test_admin_create_item_invalid(authenticated_client, app):
    """Test creating invalid assessment item fails validation."""
    response = authenticated_client.post('/admin/items', json={
        'stem': 'Short',
        'type': 'invalid_type',
        'competency': 'Invalid Competency'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'issues' in data

def test_admin_export_csv(authenticated_client, app):
    """Test CSV export functionality."""
    response = authenticated_client.get('/admin/export.csv')
    
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'

def test_admin_export_xlsx(authenticated_client, app):
    """Test Excel export functionality."""
    response = authenticated_client.get('/admin/export.xlsx')
    
    assert response.status_code == 200
