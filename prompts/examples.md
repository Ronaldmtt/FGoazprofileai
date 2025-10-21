# Exemplos de Prompts e Rubricas

Este documento contém exemplos de prompts, rubricas de correção e variações de itens para o OAZ IA Profiler.

## Rubricas de Correção para Questões Abertas

### Exemplo 1: Fundamentos de IA

**Questão**: Explique brevemente o conceito de "fine-tuning" em modelos de IA.

**Rubrica**:
```json
{
  "relevancia": "Menciona ajuste de modelo pré-treinado para tarefa específica",
  "precisao": "Explica uso de dados específicos do domínio",
  "completude": "Menciona melhoria de performance em tarefa específica",
  "objetividade": "Resposta clara e direta, sem divagações"
}
```

**Resposta Excelente (Score: 0.9-1.0)**:
> Fine-tuning é o processo de ajustar um modelo de IA pré-treinado usando dados específicos do domínio para melhorar sua performance em uma tarefa específica, como classificação de textos médicos ou tradução técnica.

**Resposta Boa (Score: 0.7-0.8)**:
> Fine-tuning é quando você pega um modelo já treinado e treina de novo com seus próprios dados para ele ficar melhor na sua tarefa específica.

**Resposta Média (Score: 0.5-0.6)**:
> É quando você treina um modelo de IA de novo.

**Resposta Fraca (Score: 0.0-0.4)**:
> Não sei exatamente.

---

### Exemplo 2: Prompt Engineering

**Questão**: Escreva um prompt para um LLM extrair os principais insights de um relatório de vendas trimestral.

**Rubrica**:
```json
{
  "relevancia": "Prompt direcionado para extração de insights",
  "precisao": "Especifica formato de saída ou pontos-chave desejados",
  "completude": "Inclui contexto sobre o relatório e suas características",
  "objetividade": "Prompt claro, estruturado e acionável",
  "seguranca": "Não solicita informações sensíveis ou confidenciais"
}
```

**Prompt Excelente (Score: 0.9-1.0)**:
```
Analise o relatório de vendas trimestral anexo e extraia os 5 principais insights.

Para cada insight, forneça:
1. Título do insight
2. Descrição em 1-2 frases
3. Dados de suporte (números específicos)
4. Impacto no negócio (Alto/Médio/Baixo)
5. Ação recomendada

Formate a resposta como JSON com a estrutura:
{
  "insights": [
    {
      "titulo": "...",
      "descricao": "...",
      "dados": "...",
      "impacto": "...",
      "acao": "..."
    }
  ]
}

Foque em:
- Variações significativas vs trimestre anterior
- Produtos/regiões de melhor e pior performance
- Tendências emergentes
- Oportunidades e riscos
```

**Prompt Bom (Score: 0.7-0.8)**:
```
Analise este relatório de vendas e me dê os principais insights.

Liste:
- Principais mudanças
- Produtos que mais venderam
- Problemas identificados
- Recomendações

Formato: lista numerada
```

**Prompt Médio (Score: 0.5-0.6)**:
```
Leia o relatório de vendas e me diga o que é importante.
```

**Prompt Fraco (Score: 0.0-0.4)**:
```
Resumo do relatório.
```

---

### Exemplo 3: Automação de Processos

**Questão**: Descreva um processo na sua área que poderia ser parcialmente automatizado com IA e como você o faria.

**Rubrica**:
```json
{
  "relevancia": "Identifica processo claro e viável para automação",
  "precisao": "Descreve etapas específicas de como seria a automação",
  "completude": "Considera validação humana, riscos ou limitações",
  "praticidade": "Solução factível com tecnologia atual",
  "criatividade": "Demonstra pensamento aplicado ao contexto real"
}
```

**Resposta Excelente (Score: 0.9-1.0)**:
> No atendimento ao cliente, podemos automatizar a triagem inicial de tickets. O processo seria: (1) Sistema recebe email/chat, (2) LLM classifica tipo de problema e urgência, (3) Extrai informações-chave (número do pedido, produto, etc), (4) Direciona para departamento correto com resumo estruturado, (5) Casos complexos ou sensíveis vão para humano revisar. Isso reduziria tempo de primeira resposta de 2h para 5min, mas manteria humano na decisão final.

**Resposta Boa (Score: 0.7-0.8)**:
> Podemos automatizar a geração de relatórios semanais. Um script coleta dados do sistema, LLM gera análise e insights, e envia por email. Humano revisa antes de enviar para diretoria.

**Resposta Média (Score: 0.5-0.6)**:
> Automatizar respostas de email usando ChatGPT.

**Resposta Fraca (Score: 0.0-0.4)**:
> Usar IA para tudo.

---

## Variações de Itens

### Questão Base: O que significa RAG?

**Variação 1 (Fácil)**:
> O que significa a sigla RAG no contexto de IA generativa?
> 
> A) Retrieval-Augmented Generation
> B) Random Access Generator
> C) Rapid AI Growth
> D) Real-time Analytics Gateway

**Variação 2 (Médio)**:
> Qual é o principal benefício de usar RAG em sistemas de Q&A?
> 
> A) Reduz custos de armazenamento
> B) Permite respostas baseadas em conhecimento atualizado sem retreinar o modelo
> C) Aumenta a velocidade de geração
> D) Elimina a necessidade de prompts

**Variação 3 (Difícil - Cenário)**:
> Você está desenvolvendo um chatbot para atendimento ao cliente que precisa responder sobre 10.000 produtos atualizados diariamente. Qual abordagem RAG seria mais eficiente?
> 
> A) Incluir todos os 10k produtos em cada prompt
> B) Criar embeddings dos produtos, indexar em vector DB, recuperar top-5 relevantes por query
> C) Retreinar o modelo diariamente com novos produtos
> D) Usar apenas busca por keywords no Google

---

## Prompts para Agentes Internos

### AgentGrader - Scoring de Resposta Aberta

```
Você é um avaliador especializado em IA. Avalie a seguinte resposta baseado na rubrica fornecida.

QUESTÃO:
{item.stem}

RESPOSTA DO CANDIDATO:
{user_answer}

RUBRICA:
{rubric}

Retorne uma avaliação estruturada em JSON:
{
  "score": <float 0-1>,
  "breakdown": {
    "relevancia": <float 0-1>,
    "precisao": <float 0-1>,
    "completude": <float 0-1>,
    "objetividade": <float 0-1>
  },
  "flags": {
    "too_short": <bool>,
    "off_topic": <bool>,
    "incomplete": <bool>
  },
  "feedback": "<1-2 frases de feedback construtivo>"
}

Seja rigoroso mas justo. Considere o nível de profundidade esperado para uma avaliação profissional.
```

---

### AgentSelector - Seleção de Próximo Item

```
Dado o perfil atual do candidato, selecione o próximo item ideal para maximizar informação.

PERFIL ATUAL:
{proficiency_state}

HISTÓRICO:
{response_history}

ITENS DISPONÍVEIS:
{available_items}

CRITÉRIOS DE SELEÇÃO:
1. Priorizar competências com maior incerteza (CI alto)
2. Selecionar dificuldade próxima ao score atual
3. Diversificar tipos de questão
4. Evitar repetir mesma competência consecutivamente
5. Considerar discriminação do item (a > 0.6 preferível)

Retorne:
{
  "selected_item_id": <int>,
  "reasoning": "<por que este item foi escolhido>",
  "expected_information_gain": <float 0-1>
}
```

---

### AgentRecommender - Geração de Trilhas

```
Com base no perfil de proficiência final do candidato, gere trilhas de aprendizado personalizadas.

PERFIL:
{proficiency_snapshot}

GAPS IDENTIFICADOS:
{competencies_below_threshold}

Para cada gap, crie uma trilha de aprendizado com:
1. Título da trilha
2. Nível atual → Nível alvo
3. 3-5 recursos recomendados (cursos, artigos, práticas)
4. Ordem de prioridade baseada na severidade do gap

Foque em recursos práticos e acionáveis. Priorize gaps em competências fundamentais.

Formato JSON:
{
  "tracks": [
    {
      "competency": "...",
      "current_level": "N1",
      "target_level": "N2",
      "priority": "Alta",
      "resources": [
        "Curso: ...",
        "Prática: ...",
        "Leitura: ..."
      ]
    }
  ],
  "summary": "<mensagem motivacional de 1-2 frases>"
}
```

---

## Exemplos de Questões por Tipo

### MCQ (Múltipla Escolha)

```json
{
  "stem": "Qual das seguintes NÃO é uma característica dos modelos GPT?",
  "type": "mcq",
  "competency": "Fundamentos de IA/ML & LLMs",
  "difficulty_b": 1,
  "discrimination_a": 0.7,
  "choices": [
    "Processamento de linguagem natural",
    "Geração de texto baseada em contexto",
    "Determinístico (sempre gera a mesma resposta)",
    "Treinamento com grandes volumes de dados"
  ],
  "answer_key": "C"
}
```

### Cenário Prático

```json
{
  "stem": "Você precisa resumir 50 PDFs de pesquisa. Qual abordagem seria mais eficiente com IA?",
  "type": "scenario",
  "competency": "Ferramentas de IA no dia a dia",
  "difficulty_b": 1,
  "discrimination_a": 0.7,
  "choices": [
    "Copiar e colar cada PDF no ChatGPT manualmente",
    "Usar uma ferramenta com processamento em lote (batch) e RAG",
    "Pedir para o ChatGPT 'resumir 50 PDFs'",
    "Ler todos manualmente e depois pedir resumo"
  ],
  "answer_key": "B"
}
```

### Prompt Writing

```json
{
  "stem": "Escreva um prompt para extrair entidades (pessoas, organizações, locais) de um artigo de notícias.",
  "type": "prompt_writing",
  "competency": "Prompt Engineering & Orquestração",
  "difficulty_b": 2,
  "discrimination_a": 0.7,
  "rubric": {
    "relevancia": "Prompt focado em extração de entidades",
    "precisao": "Especifica tipos de entidades desejadas",
    "completude": "Inclui formato de saída estruturado",
    "objetividade": "Instruções claras e sem ambiguidade",
    "exemplos": "Fornece exemplos ou formato esperado"
  }
}
```

### Resposta Aberta

```json
{
  "stem": "Explique a importância da transparência ao usar IA em decisões que afetam pessoas (ex: crédito, contratação).",
  "type": "open_ended",
  "competency": "Ética, Segurança & Compliance",
  "difficulty_b": 2,
  "discrimination_a": 0.7,
  "rubric": {
    "relevancia": "Aborda transparência e explicabilidade de decisões",
    "precisao": "Menciona direitos, regulamentação (LGPD, etc) ou impactos concretos",
    "completude": "Explica impacto em confiança, justiça ou accountability",
    "etica": "Demonstra consciência de implicações éticas"
  }
}
```

---

## Templates de Feedback

### Feedback Positivo
```
Excelente! Sua resposta demonstra {competency_strong_point}. 
Continue aprofundando em {next_topic}.
```

### Feedback Construtivo
```
Boa tentativa! Para melhorar, foque em {improvement_area}. 
Considere explorar {resource_suggestion}.
```

### Feedback de Gaps
```
Identificamos oportunidade de desenvolvimento em {competency}.
Recomendamos: {learning_track}.
```

---

**Nota**: Estes exemplos servem como guia para criação de novos itens e podem ser adaptados conforme necessidade.
