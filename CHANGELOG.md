# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.0.0] - 2025-10-21

### ✨ Features Implementadas

#### Autenticação e Segurança
- ✅ Sistema de magic link para autenticação sem senha
- ✅ Validação de domínio de email (@oaz.co)
- ✅ Consentimento LGPD obrigatório para novos usuários
- ✅ Tokens JWT com expiração configurável (24h)
- ✅ Sanitização de inputs para prevenir XSS
- ✅ Audit logging de todas as ações críticas

#### Avaliação Adaptativa
- ✅ Sistema IRT-lite para scoring de proficiência
- ✅ 9 competências de IA avaliadas
- ✅ Pergunta inicial (P0) para calibração
- ✅ Seleção adaptativa de próximo item baseada em:
  - Proficiência atual
  - Intervalo de confiança
  - Diversificação de tipos e competências
  - Maximização de informação
- ✅ Critérios de parada automáticos:
  - Máximo 12 itens
  - Mínimo 8 itens  
  - Convergência (CI ≤ 12 em 6+ competências)
  - Timeout de 12 minutos

#### Ecossistema de Agentes
- ✅ **AgentOrchestrator**: Coordenação central do fluxo
- ✅ **AgentProfiler**: Inicialização de perfil de proficiência
- ✅ **AgentSelector**: Seleção ótima de próximo item
- ✅ **AgentGrader**: Correção de MCQ e respostas abertas
- ✅ **AgentScorer**: Atualização de scores via IRT-lite
- ✅ **AgentRecommender**: Geração de trilhas de aprendizado
- ✅ **AgentGenerator**: Geração de variações de itens (preparado)
- ✅ **AgentContentQA**: Validação de qualidade de itens

#### Banco de Itens
- ✅ Seed automático com 36+ itens de avaliação
- ✅ 4 tipos de questões:
  - MCQ (múltipla escolha)
  - Cenário prático
  - Prompt writing
  - Resposta aberta
- ✅ Metadata completa:
  - Dificuldade (0-2)
  - Discriminação (0-1)
  - Tags
  - Rubricas de correção

#### Dashboard Administrativo
- ✅ Overview com métricas gerais:
  - Total de usuários
  - Avaliações concluídas
  - Taxa de participação
  - Sessões em andamento
- ✅ Distribuição de níveis (N0-N5)
- ✅ Heatmap de competências
- ✅ Filtros por departamento
- ✅ CRUD completo de itens:
  - Listagem
  - Criação com validação
  - Edição
  - Desativação
- ✅ Exportação de dados:
  - CSV
  - Excel (XLSX)
- ✅ Visualização detalhada por usuário

#### Frontend Responsivo
- ✅ Templates Jinja2 + HTMX + Alpine.js
- ✅ Tailwind CSS para estilização
- ✅ Páginas implementadas:
  - Login com magic link
  - Consentimento LGPD
  - Início de avaliação (P0)
  - Apresentação de itens com progress bar
  - Finalização
  - Resultado com scores e recomendações
  - Dashboard administrativo
  - Gerenciamento de itens
- ✅ Interatividade sem page reload (HTMX)
- ✅ Validação client-side (Alpine.js)

#### Sistema de Scoring
- ✅ IRT-lite implementation:
  - Update baseado em dificuldade do item
  - Redução de CI com mais respostas
  - Cálculo de nível global (N0-N5)
- ✅ Correção automática:
  - MCQ: determinística por gabarito
  - Abertas: scoring por LLM stub com rubricas
- ✅ Snapshot de proficiência final
- ✅ Geração de recomendações personalizadas

#### Database e ORM
- ✅ Modelos SQLAlchemy:
  - User (com consentimento LGPD)
  - Session (com status e timing)
  - Item (com metadata IRT)
  - Response (com scoring e flags)
  - ProficiencySnapshot
  - Recommendation
  - Audit
- ✅ SQLite para desenvolvimento
- ✅ Preparado para PostgreSQL (variável DATABASE_URL)
- ✅ Migrações Alembic (preparadas)

#### LLM Provider Abstraction
- ✅ Interface abstrata para LLM operations
- ✅ Implementação stub determinística (MVP)
- ✅ Operações suportadas:
  - generate(): Geração de texto
  - score(): Scoring de respostas
  - moderate(): Moderação de conteúdo
- ✅ Preparado para OpenAI/Azure (futuro)

#### Serviços
- ✅ Email service (console logging em dev)
- ✅ Exporter service (CSV e XLSX)
- ✅ Audit logging centralizado

#### Testes
- ✅ Suite pytest com 21 testes
- ✅ Cobertura de testes:
  - Auth: magic link, validação domínio, LGPD
  - Flow: início, respostas, finalização
  - Scoring: IRT, grading, convergência
  - Admin: dashboard, CRUD, exports
- ✅ 20/21 testes passando (95%+)
- ✅ Fixtures para setup de ambiente de teste

### 🏗️ Arquitetura

#### Estrutura de Diretórios
```
app/
├── agents/       # Ecossistema de agentes internos
├── core/         # Módulos principais (scoring, security, LLM)
├── models/       # ORM models
├── routes/       # Flask blueprints
├── services/     # Email, export, etc
├── templates/    # Jinja2 templates
└── tests/        # Pytest tests
```

#### Padrões Utilizados
- **MVC**: Separação models/routes/templates
- **Dependency Injection**: Config como parâmetro
- **Factory Pattern**: create_app()
- **Strategy Pattern**: LLM provider abstraction
- **Repository Pattern**: ORM models

### 📦 Dependências

#### Backend
- Flask 3.0
- SQLAlchemy 2.0  
- Flask-SQLAlchemy 3.1
- Pydantic 2.5
- python-dotenv 1.0
- email-validator 2.1
- itsdangerous 2.2

#### Testing
- pytest 7.4
- pytest-cov 4.1

#### Data Export
- openpyxl 3.1
- pandas 2.1

### 🔧 Configuração

#### Variáveis de Ambiente
- `APP_SECRET` / `SESSION_SECRET`: Chave secreta
- `ALLOWED_EMAIL_DOMAIN`: Domínio permitido (default: oaz.co)
- `SEED_ON_START`: Auto-seed (default: 1)
- `FLASK_ENV`: Ambiente (default: development)
- `FLASK_DEBUG`: Debug mode (default: 1)
- `BASE_URL`: URL base (default: http://localhost:5000)

#### Configurações de Avaliação
- `MAX_ITEMS_PER_SESSION`: 12
- `MIN_ITEMS_PER_SESSION`: 8
- `TARGET_SESSION_TIME_MINUTES`: 12
- `CONVERGENCE_CI_THRESHOLD`: 12
- `CONVERGENCE_MIN_COMPETENCIES`: 6
- `TOKEN_EXPIRATION_HOURS`: 24

### 📝 Documentação
- ✅ README.md completo
- ✅ CHANGELOG.md
- ✅ Docstrings em todos os módulos
- ✅ Comentários inline em lógica complexa
- ✅ Exemplos de uso

### 🚀 Deploy
- ✅ Workflow configurado para Replit
- ✅ Servidor Flask em 0.0.0.0:5000
- ✅ Hot reload em desenvolvimento
- ✅ Seed automático na primeira execução

### 🔒 Segurança
- ✅ Validação de email com domínio
- ✅ Sanitização de inputs
- ✅ CSRF protection (Flask built-in)
- ✅ Secure session cookies
- ✅ No external LLM calls (stub implementation)
- ✅ Audit trail completo

### 📊 Métricas
- 36 itens de avaliação (seed)
- 9 competências avaliadas
- 6 tipos de endpoints
- 7 agentes internos
- 7 modelos ORM
- 21 testes automatizados
- ~2500 linhas de código Python
- ~500 linhas de templates

## [Futuro] - Roadmap

### V1.1 - LLM Integration
- [ ] Integração OpenAI/Azure
- [ ] Grading avançado de respostas abertas
- [ ] Geração dinâmica de questões

### V1.2 - Async Processing
- [ ] Celery + Redis
- [ ] Background jobs
- [ ] Email real (SendGrid)

### V1.3 - Enhanced Analytics
- [ ] Time-series de evolução
- [ ] Comparação entre cohorts
- [ ] Métricas avançadas

### V1.4 - Semantic Search
- [ ] pgvector integration
- [ ] Embeddings para itens
- [ ] Seleção semântica

### V1.5 - Anti-fraude
- [ ] Análise de timing patterns
- [ ] Detecção de copy-paste
- [ ] IP tracking

---

**Formato**: Baseado em [Keep a Changelog](https://keepachangelog.com/)  
**Versionamento**: [Semantic Versioning](https://semver.org/)
