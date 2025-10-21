# Guia Rápido - OAZ IA Profiler

## Início Rápido (5 minutos)

### 1. Acesse a aplicação
A aplicação está rodando em: **http://localhost:5000**

### 2. Faça login
1. Digite um email do domínio **@oaz.co** (ex: `seu.nome@oaz.co`)
2. Clique em "Entrar"
3. **Pronto!** O sistema valida seu domínio e faz login automaticamente
4. Se for novo usuário, você será redirecionado para aceitar os termos LGPD

### 3. Aceite os Termos LGPD
- Leia e aceite o consentimento de uso de dados
- Preencha: Nome completo, Departamento, Cargo

### 4. Faça a Avaliação
1. **Pergunta Inicial (P0)**: Responda a primeira pergunta para calibração
2. **Avaliação Adaptativa**: Responda 8-12 perguntas (dificuldade ajustada dinamicamente)
3. **Tipos de questão**:
   - Múltipla escolha
   - Cenários práticos
   - Escrita de prompts
   - Respostas abertas

### 5. Veja seus Resultados
- **Nível Global**: N0 (Iniciante) a N5 (Master)
- **Score por competência**: 0-100 para cada uma das 9 competências
- **Trilhas de aprendizado**: Recomendações personalizadas baseadas em gaps

---

## Para Administradores

### Acesse o Dashboard Admin
```
http://localhost:5000/admin
```

**Funcionalidades**:
- 📊 Overview com métricas gerais
- 🔥 Heatmap de competências
- 👥 Drill-down por departamento/cargo
- ➕ Criar/Editar itens de avaliação
- 📥 Exportar dados (CSV/XLSX)

### Exportar Dados

**CSV**:
```bash
curl http://localhost:5000/admin/export.csv > resultados.csv
```

**Excel**:
```bash
curl http://localhost:5000/admin/export.xlsx > resultados.xlsx
```

---

## Executando Localmente

### Pré-requisitos
- Python 3.11+
- pip

### Passos

1. **Clone e instale**:
```bash
git clone <repo-url>
cd oaz-ia-profiler
pip install -r requirements.txt
```

2. **Execute**:
```bash
python app.py
```

3. **Acesse**:
```
http://localhost:5000
```

---

## Executando Testes

### Todos os testes
```bash
pytest app/tests/ -v
```

### Com cobertura
```bash
pytest app/tests/ -v --cov=app --cov-report=html
```

### Apenas um módulo
```bash
pytest app/tests/test_auth.py -v
```

---

## Configuração Avançada

### Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# Segurança
APP_SECRET=seu-secret-key-super-seguro
SESSION_SECRET=outro-secret-diferente

# Email
ALLOWED_EMAIL_DOMAIN=oaz.co
SENDGRID_API_KEY=SG.xxxxx  # Opcional: para envio real de emails

# App
BASE_URL=http://localhost:5000
FLASK_ENV=development
FLASK_DEBUG=1

# Database
SEED_ON_START=1  # Auto-seed na primeira execução
```

### Ajustar Parâmetros de Avaliação

Edite `config.py`:

```python
MAX_ITEMS_PER_SESSION = 12        # Máximo de perguntas
MIN_ITEMS_PER_SESSION = 8         # Mínimo de perguntas
TARGET_SESSION_TIME_MINUTES = 12  # Tempo alvo
CONVERGENCE_CI_THRESHOLD = 12     # Threshold de convergência
```

---

## Solução de Problemas

### Erro: "Email deve ser do domínio @oaz.co"
**Solução**: Use apenas emails corporativos @oaz.co

### Erro: "ModuleNotFoundError: No module named 'X'"
**Solução**: 
```bash
pip install -r requirements.txt
```

### Banco de dados vazio
**Solução**: Certifique-se que `SEED_ON_START=1` e reinicie a aplicação

### Login não funciona
**Solução**: Verifique se o email é do domínio @oaz.co. O sistema valida automaticamente e faz login direto.

---

## Estrutura do Projeto

```
oaz-ia-profiler/
├── app/                    # Código da aplicação
│   ├── agents/            # Agentes internos (Orchestrator, Selector, etc)
│   ├── core/              # Módulos principais (scoring, security, LLM)
│   ├── models/            # Modelos de banco de dados
│   ├── routes/            # Endpoints Flask
│   ├── services/          # Serviços (email, export)
│   ├── templates/         # Templates HTML
│   └── tests/             # Testes automatizados
├── config.py              # Configurações
├── app.py                 # Entry point
├── requirements.txt       # Dependências
├── README.md              # Documentação completa
├── CHANGELOG.md           # Histórico de versões
├── QUICKSTART.md          # Este guia
└── prompts/               # Exemplos de prompts e rubricas
```

---

## Recursos Adicionais

- 📖 **Documentação Completa**: Veja `README.md`
- 📝 **Histórico de Mudanças**: Veja `CHANGELOG.md`
- 💡 **Exemplos de Prompts**: Veja `prompts/examples.md`

---

## Suporte

Para dúvidas ou problemas:
1. Consulte a documentação completa no `README.md`
2. Verifique os logs da aplicação
3. Entre em contato com a equipe inovAI.lab

---

**Boa avaliação! 🚀**
