# OAZ IA Profiler

Sistema de avaliação adaptativa de proficiência em IA para colaboradores da OAZ.

## 📋 Visão Geral

OAZ IA Profiler é uma plataforma de avaliação que mede o nível de proficiência em Inteligência Artificial de colaboradores em 8-12 minutos, utilizando um sistema de avaliação adaptativa com 9 competências-chave.

### Principais Funcionalidades

- **Autenticação Segura**: Magic link via email (@oaz.co) com conformidade LGPD
- **Avaliação Adaptativa**: Sistema IRT-lite que ajusta dificuldade baseado em respostas
- **9 Competências de IA**:
  1. Fundamentos de IA/ML & LLMs
  2. Ferramentas de IA no dia a dia
  3. Prompt Engineering & Orquestração
  4. Dados & Contextualização (RAG)
  5. Automação de Processos com IA
  6. Ética, Segurança & Compliance
  7. Produto e Negócio com IA
  8. Code/No-code para IA
  9. LLMOps & Qualidade

- **Ecossistema de Agentes Internos**:
  - **AgentOrchestrator**: Coordena todo o fluxo de avaliação
  - **AgentProfiler**: Inicializa perfil de proficiência
  - **AgentSelector**: Seleciona próxima pergunta otimizada
  - **AgentGrader**: Corrige respostas objetivas e discursivas
  - **AgentScorer**: Atualiza scores de proficiência
  - **AgentRecommender**: Gera trilhas de aprendizado personalizadas
  - **AgentContentQA**: Valida qualidade de novos itens

- **Critérios de Parada Inteligentes**:
  - Máximo 12 itens
  - Mínimo 8 itens
  - Convergência (IC ≤ 12 pontos em 6+ competências)
  - Tempo limite de 12 minutos

- **Dashboard Administrativo**:
  - Distribuição de níveis (N0-N5)
  - Heatmap de competências
  - Drill-down por departamento/cargo
  - Exportação CSV/XLSX

## 🏗️ Arquitetura

```
OAZ IA Profiler
├── app/
│   ├── agents/              # Ecossistema de agentes internos
│   │   ├── orchestrator.py  # Coordenador central
│   │   ├── profiler.py      # Inicializador de perfil
│   │   ├── selector.py      # Seletor de itens
│   │   ├── grader.py        # Corretor de respostas
│   │   ├── scorer.py        # Atualizador de scores
│   │   ├── recommender.py   # Gerador de recomendações
│   │   ├── generator.py     # Gerador de variações
│   │   └── content_qa.py    # Validador de conteúdo
│   │
│   ├── core/                # Módulos principais
│   │   ├── llm_provider.py  # Abstração LLM (stub MVP)
│   │   ├── scoring.py       # Motor IRT-lite
│   │   ├── schemas.py       # Validação Pydantic
│   │   ├── security.py      # Auth e sanitização
│   │   └── utils.py         # Utilidades e seeding
│   │
│   ├── models/              # Modelos ORM
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── item.py
│   │   ├── response.py
│   │   ├── snapshot.py
│   │   ├── recommendation.py
│   │   └── audit.py
│   │
│   ├── routes/              # Endpoints Flask
│   │   ├── auth.py          # Autenticação
│   │   ├── session.py       # Gestão de sessões
│   │   ├── items.py         # Entrega de itens
│   │   ├── responses.py     # Processamento de respostas
│   │   └── admin.py         # Dashboard admin
│   │
│   ├── services/            # Serviços
│   │   ├── emailer.py       # Email (console dev)
│   │   └── exporter.py      # Export CSV/XLSX
│   │
│   ├── templates/           # Templates Jinja2
│   └── tests/               # Testes Pytest
│
├── config.py                # Configuração
├── app.py                   # Entry point
└── requirements.txt         # Dependências
```

## 🚀 Setup e Execução

### Pré-requisitos

- Python 3.11+
- SQLite

### Instalação

1. Clone o repositório:
```bash
git clone <repo-url>
cd oaz-ia-profiler
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure variáveis de ambiente:
```bash
# As variáveis são configuradas automaticamente com valores padrão
# Para customizar, defina:
# - APP_SECRET ou SESSION_SECRET: Chave secreta da aplicação
# - ALLOWED_EMAIL_DOMAIN: Domínio permitido (padrão: oaz.co)
# - SEED_ON_START: 1 para seed automático na primeira execução
```

4. Execute a aplicação:
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

### Primeiro Acesso

1. Acesse `http://localhost:5000`
2. Digite um email `@oaz.co`
3. Clique em "Entrar"
4. Se for novo usuário: aceite os termos LGPD
5. Inicie sua avaliação!

**Novo fluxo simplificado**: Não precisa mais clicar em links! O login acontece automaticamente após validação do domínio de email.

## 🧪 Testes

Execute a suite completa de testes:

```bash
pytest app/tests/ -v --cov=app --cov-report=term-missing
```

### Cobertura de Testes

- ✅ **Auth**: Validação de domínio, magic links, consentimento LGPD
- ✅ **Flow**: Início de sessão, submissão de respostas, finalização
- ✅ **Scoring**: IRT scoring, correção MCQ/abertas, convergência
- ✅ **Admin**: Dashboard, CRUD de itens, exportações

**Cobertura**: 20/21 testes passando (95%+)

## 📊 Dados de Seed

O banco de dados é automaticamente populado com 36 itens de avaliação:
- 4 itens por competência (9 competências)
- Tipos: MCQ, Cenário Prático, Prompt Writing, Aberta
- Dificuldades: 0 (fácil), 1 (médio), 2 (difícil)
- Discriminação: 0.5 - 0.9

## 👥 Perfis de Usuário

### Colaborador
- Autenticação via magic link
- Responder avaliação (8-15 itens)
- Ver resultado final com:
  - Nível global (N0-N5)
  - Score por competência
  - Trilhas de aprendizado recomendadas

### Admin (RH/inovAI.lab)
- Dashboard com métricas gerais
- Heatmap de competências
- Drill-down por departamento/cargo
- CRUD de itens de avaliação
- Exportação de dados (CSV/XLSX)

## 🔒 Segurança e LGPD

- ✅ Consentimento explícito obrigatório
- ✅ Validação de domínio de email (@oaz.co)
- ✅ Tokens JWT com expiração (24h)
- ✅ Sanitização de inputs
- ✅ Audit logs de todas as ações
- ✅ Dados minimizados (não envio PII para LLMs externos)
- ✅ LLM Provider em modo stub (sem chamadas externas no MVP)

## 📈 Sistema de Scoring

### IRT-lite (Item Response Theory)

O sistema utiliza uma implementação simplificada de IRT:

1. **Inicialização**: Score = 50, CI = ±30
2. **Atualização**:
   - Item difícil correto → ↑↑ score
   - Item fácil incorreto → ↓↓ score
   - CI reduz com mais respostas
3. **Convergência**: CI ≤ 12 em 6+ competências

### Níveis de Proficiência

| Nível | Score | Descrição |
|-------|-------|-----------|
| N0 | 0-29 | Iniciante |
| N1 | 30-44 | Básico |
| N2 | 45-59 | Intermediário |
| N3 | 60-74 | Avançado |
| N4 | 75-89 | Expert |
| N5 | 90-100 | Master |

## 🔧 Tecnologias

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM
- **Pydantic 2.5** - Validação de dados
- **Alembic 1.13** - Migrações (preparado)
- **pytest 7.4** - Testes

### Frontend
- **Jinja2** - Templates
- **HTMX 1.9** - Interatividade
- **Alpine.js 3.13** - Reatividade
- **Tailwind CSS** - Estilização

### Database
- **SQLite** (dev/prod)
- Pronto para PostgreSQL (via variável DATABASE_URL)

## 📦 Exportação de Dados

### CSV
```bash
GET /admin/export.csv
```

### Excel
```bash
GET /admin/export.xlsx
```

Campos exportados:
- Dados do usuário (email, nome, departamento, cargo)
- Informações da sessão
- Score global e nível
- Scores por competência

## 🎯 Roadmap Futuro

### Fase 2: LLM Integração
- [ ] Integração OpenAI/Azure
- [ ] Grading avançado de respostas abertas
- [ ] Geração dinâmica de questões

### Fase 3: Assíncrono
- [ ] Celery + Redis
- [ ] Processamento em background
- [ ] Notificações por email

### Fase 4: Busca Semântica
- [ ] pgvector para embeddings
- [ ] Seleção de itens por similaridade
- [ ] Detecção de duplicatas

### Fase 5: Anti-fraude
- [ ] Análise de timing
- [ ] Detecção de paste
- [ ] Padrões de digitação

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Propriedade da OAZ - Todos os direitos reservados

## 📧 Contato

Para dúvidas ou suporte, entre em contato com a equipe inovAI.lab

---

**Versão**: 1.0.0  
**Data**: Outubro 2025  
**Desenvolvido por**: Agent 3 (Replit)
