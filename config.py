import os
from dotenv import load_dotenv

load_dotenv()

_active_db_uri = None

def test_postgres_connection(database_url, timeout=5):
    """Test if PostgreSQL is reachable."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(
            database_url,
            connect_args={'connect_timeout': timeout}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as e:
        print(f"[CONFIG] PostgreSQL connection failed: {e}")
        return False

def get_database_uri():
    """Get database URI - try PostgreSQL, fallback to SQLite if unavailable."""
    global _active_db_uri
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if test_postgres_connection(database_url):
            print("[CONFIG] Using PostgreSQL database")
            _active_db_uri = database_url
            return database_url
        else:
            print("[CONFIG] PostgreSQL unavailable, falling back to SQLite")
    _active_db_uri = 'sqlite:///oaz_profiler.db'
    return _active_db_uri

def get_engine_options():
    """Get SQLAlchemy engine options based on active database."""
    global _active_db_uri
    if _active_db_uri and 'postgresql' in _active_db_uri:
        return {
            'pool_pre_ping': True,
            'pool_size': 5,
            'max_overflow': 10,
            'pool_recycle': 300,
            'pool_timeout': 30,
            'connect_args': {'connect_timeout': 10}
        }
    return {}

class Config:
    SECRET_KEY = os.getenv('APP_SECRET', os.getenv('SESSION_SECRET', 'dev-secret-key-change-me'))
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = get_engine_options()
    
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    ALLOWED_EMAIL_DOMAIN = os.getenv('ALLOWED_EMAIL_DOMAIN', 'oaz.co')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    SEED_ON_START = os.getenv('SEED_ON_START', '1') == '1'
    
    TOKEN_EXPIRATION_HOURS = 24
    MAX_ITEMS_PER_SESSION = 12
    MIN_ITEMS_PER_SESSION = 8
    TARGET_SESSION_TIME_MINUTES = 12
    CONVERGENCE_CI_THRESHOLD = 12
    CONVERGENCE_MIN_COMPETENCIES = 6
    
    COMPETENCIES = [
        'Fundamentos de IA/ML & LLMs',
        'Ferramentas de IA no dia a dia',
        'Prompt Engineering & Orquestração',
        'Dados & Contextualização (RAG)',
        'Automação de Processos com IA',
        'Ética, Segurança & Compliance',
        'Produto e Negócio com IA',
        'Code/No-code para IA',
        'LLMOps & Qualidade'
    ]
    
    LEVELS = {
        'N0': (0, 30),
        'N1': (30, 45),
        'N2': (45, 60),
        'N3': (60, 75),
        'N4': (75, 90),
        'N5': (90, 101)
    }
