import os
from dotenv import load_dotenv

load_dotenv()

def get_database_uri():
    """Get database URI - using SQLite for reliability."""
    return 'sqlite:///oaz_profiler.db'

def get_engine_options():
    """Get SQLAlchemy engine options."""
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
