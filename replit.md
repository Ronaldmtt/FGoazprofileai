# OAZ IA Profiler

## Overview

OAZ IA Profiler is an adaptive AI proficiency assessment platform that evaluates collaborators' competency in 9 AI domains through an 8-12 minute intelligent questionnaire. The system uses an IRT-lite (Item Response Theory) scoring algorithm to dynamically adjust question difficulty based on user responses, providing personalized proficiency reports and learning recommendations.

The application features a multi-agent ecosystem where specialized agents handle question selection, response grading, proficiency scoring, and recommendation generation. Assessment sessions adapt in real-time, converging on accurate proficiency estimates while minimizing test duration.

**Status**: ✅ Production ready (v1.4.0) - Sistema de pontuação corrigido com separação precisa entre níveis

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask 3.0** web application with blueprint-based modular routing
- **SQLAlchemy 2.0** ORM with SQLite database for local development
- **Pydantic** for request/response validation and data schemas
- Session management using Flask sessions with secure token-based authentication

### Authentication & Security
- **Magic link authentication** via email (no passwords) using `itsdangerous` signed tokens
- Email domain validation restricted to `@oaz.co` domain
- **LGPD compliance** with mandatory user consent tracking
- Input sanitization to prevent XSS attacks using regex-based HTML stripping
- JWT-style tokens with 24-hour expiration for magic links
- Comprehensive audit logging for all critical actions

### Multi-Agent Orchestration System
The application implements an internal agent ecosystem coordinated by `AgentOrchestrator`:

1. **AgentProfiler**: Initializes proficiency baseline from initial response (P0 question)
2. **AgentSelector**: **100% adaptive generation** - all questions generated via OpenAI based on user context (name, role, department) and performance
3. **AgentGrader**: Grades MCQ (deterministic) and open-ended responses using **GPT-4o semantic analysis** for intelligent rubric-based evaluation
4. **AgentScorer**: Updates competency scores using **corrected IRT algorithm** with proper theta scale conversion (-3 to +3) and Bayesian updates
5. **AgentRecommender**: Generates personalized learning tracks based on proficiency gaps
6. **AgentGenerator**: **Dynamically creates practical, work-focused questions** using GPT-4o - perguntas diretas e simples focadas no uso real de IA no trabalho, adequadas para todos os níveis (de quem nunca usou IA até especialistas)
7. **AgentContentQA**: Validates new assessment items for quality assurance

Each agent maintains separation of concerns while the orchestrator coordinates state management and decision flow.

### Adaptive Assessment Algorithm (IRT with Theta Scale)
- **Proficiency tracking** per competency (0-100 scale displayed, theta -3 to +3 internally) with confidence intervals
- **Dynamic difficulty adjustment** using proper IRT logistic model: P(correct) = 1/(1 + exp(-a*(theta - b)))
- **Enhanced discrimination**: Item discrimination clamped to minimum 1.0, ensuring strong separation between correct/incorrect
- **Optimized learning rate**: 1.0 multiplier (up from 0.3) for rapid convergence and clear differentiation
- Item parameters: difficulty_b (-1.0 to +1.5), discrimination_a (1.5 to 2.2)
- **Adaptive difficulty routing**: easy (score <40), medium (40-70), hard (>70)
- **Convergence criteria**: minimum 8 items, maximum 12 items, CI ≤ 12 points on 6+ competencies, or 12-minute timeout
- **Clear level separation**: N0 (<20), N1 (20-39), N2 (40-59), N3 (60-74), N4 (75-87), N5 (88+)

### Data Models
Database schema implemented with SQLAlchemy models:
- **User**: email, name, department, role, consent timestamp
- **Session**: assessment sessions with status tracking (active/completed)
- **Item**: question bank with stem, type, competency, IRT parameters, choices, rubrics
- **Response**: user answers with grading scores, latency, AI flags
- **ProficiencySnapshot**: per-competency scores with confidence intervals
- **Recommendation**: learning tracks generated post-assessment
- **Audit**: comprehensive action logging for compliance

### Frontend Architecture
- **Tailwind CSS** for responsive UI styling
- **Alpine.js** for reactive client-side interactions
- **HTMX** for progressive enhancement and AJAX requests
- Server-side rendered Jinja2 templates with component-based structure
- Real-time progress tracking and form validation

### Assessment Content Management
- **Seed database** with 36+ pre-validated assessment items on startup
- Four question types: MCQ, scenario-based, prompt writing, open-ended
- 9 competency domains covering fundamentals, tools, ethics, automation, LLMOps, etc.
- Rubric-based grading for subjective responses with multi-dimensional scoring

### Scoring & Reporting
- **Global proficiency score** calculated as weighted average across competencies
- **Level classification** (N0-N5) with threshold-based categorization
- Competency heatmaps showing strengths and gaps
- Time-spent tracking and response latency analysis
- CSV/XLSX export capabilities for administrative reporting

### LLM Integration Layer
Abstraction through `LLMProvider` class with **full OpenAI integration** (GPT-4o):
- **100% adaptive question generation**: Perguntas práticas e diretas personalizadas ao contexto do usuário (cargo, área, nível)
- **Foco no uso real de IA**: Perguntas sobre ferramentas e situações práticas do dia a dia de trabalho
- **Adequado para todos os níveis**: Desde colaboradores que nunca usaram IA até especialistas avançados
- **Objetivo corporativo**: Identificar níveis de conhecimento para direcionar treinamentos adequados
- **Semantic response evaluation**: Intelligent rubric-based grading for open-ended responses with detailed feedback
- **Content moderation**: Safety checks using OpenAI moderation API
- Uses GPT-4o model with JSON structured outputs for reliability and proper `max_completion_tokens` parameter

## External Dependencies

### Third-Party Services
- **SendGrid API** (configured but not required for MVP) - magic link email delivery
- Email validation via `email-validator` library
- Currently operates in development mode with console-based email logging

### Database
- **SQLite** for local/development storage
- Schema supports migration to PostgreSQL via SQLAlchemy's database-agnostic ORM
- JSON columns for flexible metadata storage (choices, rubrics, proficiency states)

### Python Libraries
Core dependencies from `requirements.txt`:
- Flask 3.0 + Werkzeug for web framework
- SQLAlchemy 2.0 + Alembic for ORM and migrations
- Pydantic 2.5 for schema validation
- python-dotenv for environment configuration
- itsdangerous for secure token generation
- pandas + openpyxl for data export
- pytest + pytest-cov for testing

### Environment Configuration
Managed via `.env` file with variables:
- `APP_SECRET`/`SESSION_SECRET`: Flask session encryption key
- **`OPENAI_API_KEY`**: OpenAI API key for GPT-4o integration (100% adaptive questions & semantic evaluation)
- `SENDGRID_API_KEY`: Email service authentication
- `ALLOWED_EMAIL_DOMAIN`: Domain restriction (default: oaz.co)
- `BASE_URL`: Application base URL for magic links
- `SEED_ON_START`: Auto-populate database flag
- `FLASK_ENV`, `FLASK_DEBUG`: Runtime environment settings

### Deployment Considerations
- Dockerfile support for containerization
- Replit.nix configuration for Replit environment
- Static file serving via Flask development server (use reverse proxy in production)
- Session storage currently in-memory (migrate to Redis/database for production scaling)