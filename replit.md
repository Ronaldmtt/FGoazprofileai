# OAZ IA Profiler

## Overview

OAZ IA Profiler is an AI maturity assessment platform that evaluates employees' proficiency across 4 key dimensions through a streamlined 10-question assessment. The system uses **100% OpenAI-generated questions** personalized to each user's role and department, with a simplified scoring model (10-40 points) that classifies employees into 4 maturity levels to direct them to appropriate training programs.

The application features a multi-agent ecosystem where specialized agents handle question generation, response grading, and maturity classification. All questions are generated dynamically via GPT-4o, ensuring relevance and practical focus on real-world AI tool usage.

**Status**: ✅ Production ready (v2.0.0) - Simplified matrix-based assessment with 4-block structure and 100% adaptive question generation

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

### Multi-Agent Orchestration System (Matrix-Based)
The application implements a simplified agent ecosystem coordinated by `AgentOrchestratorMatrix`:

1. **AgentSelectorMatrix**: Manages question distribution across 4 blocks with predetermined counts (10 questions total)
2. **AgentGenerator**: **100% dynamic question generation** using GPT-4o with:
   - **Personalization**: Questions adapted to user's name, role, and department
   - **Progressive difficulty**: Choices A/B/C/D represent increasing maturity levels (1-4 points)
   - **Practical focus**: Questions about real-world AI tool usage and scenarios
   - **Enhanced prompts** for creating subtle, overlapping alternatives (not obvious correct answers)
   - **Distractor quality control** - options are plausible and represent different maturity levels
   - **Length balance** - all choices have similar length (±30% variance)
3. **AgentGraderMatrix**: Simple deterministic grading mapping A=1, B=2, C=3, D=4 points
4. **SemanticValidator**: Quality assurance for generated questions (optional, can be enabled for stricter validation)

Each agent maintains separation of concerns while the orchestrator coordinates state management and scoring flow.

### Simplified Matrix Assessment Algorithm
- **4-Block Structure** (`blocks_config.py`):
  1. **Percepção e Atitude** (3 questions): Awareness and attitude toward AI
  2. **Uso Prático** (3 questions): Practical use of AI tools in daily work
  3. **Conhecimento e Entendimento** (2 questions): Technical understanding of AI concepts
  4. **Cultura e Autonomia Digital** (2 questions): Digital culture and autonomy
- **Simple Scoring**: Each question has 4 choices (A/B/C/D) = 1/2/3/4 points representing progressive maturity
- **Total Score Range**: 10-40 points (10 questions × 4 max points)
- **4 Maturity Levels**:
  1. **Iniciante** (10-17 pts): Beginning AI journey, basic awareness
  2. **Explorador** (18-27 pts): Occasional AI use, understanding benefits
  3. **Praticante** (28-35 pts): Daily AI use, technical understanding
  4. **Líder Digital** (36-40 pts): AI reference, strategic thinking, cultural transformation

### Data Models
Database schema implemented with SQLAlchemy models (matrix-based):
- **User**: email, name, department, role, consent timestamp
- **Session**: assessment sessions with status tracking (active/completed)
- **Item**: dynamically generated questions with stem, block (instead of competency), progressive_levels flag, choices
- **Response**: user answers with matrix_points (1-4), graded_score_0_1 (normalized)
- **ProficiencySnapshot**: total raw_score (10-40), maturity_level, block_scores (JSON)
- **Audit**: comprehensive action logging for compliance

### Frontend Architecture
- **Tailwind CSS** for responsive UI styling
- **Alpine.js** for reactive client-side interactions
- **HTMX** for progressive enhancement and AJAX requests
- Server-side rendered Jinja2 templates with component-based structure
- Real-time progress tracking and form validation

### Assessment Content Management
- **100% dynamic generation**: No pre-seeded questions - all generated on-demand via OpenAI
- **Personalization**: Each question tailored to user's role and department
- **4 question blocks**: Distributed across Percepção, Uso Prático, Conhecimento, Cultura
- **Progressive choice design**: Options A/B/C/D represent increasing maturity (1-4 points)

### Scoring & Reporting
- **Simple additive scoring**: Sum of points across 10 questions (10-40 range)
- **Maturity level classification**: 4 levels (Iniciante, Explorador, Praticante, Líder Digital)
- **Block breakdown**: Performance visualization per block
- **Training direction**: Results used to direct employees to appropriate AI training programs
- Time-spent tracking and response latency analysis
- CSV/XLSX export capabilities for administrative reporting

### LLM Integration Layer
**100% OpenAI-powered** question generation and quality control via `LLMProvider` class:
- **Dynamic question generation** (`generate_matrix_question`):
  - **Personalization**: Uses user name, role, department for context-aware questions
  - **Progressive maturity design**: Choices A/B/C/D represent 1/2/3/4 maturity levels
  - **Practical focus**: Questions about real-world AI tool usage scenarios
  - **Quality prompts**: Enhanced prompts for subtle, overlapping alternatives (no obvious answers)
  - **Distractor control**: Options are plausible and represent different maturity stages
  - **Length balance**: All choices similar length (±30% variance)
- **Block-specific generation**: Questions tailored to each of the 4 blocks (Percepção, Uso Prático, Conhecimento, Cultura)
- **Retry logic**: Up to 3 generation attempts if quality validation fails
- **Embeddings API**: text-embedding-3-small for semantic distance validation (optional)
- Uses GPT-4o model with JSON structured outputs for reliability and proper `max_completion_tokens` parameter
- **Corporate focus**: Questions designed to identify precise maturity levels for training direction

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