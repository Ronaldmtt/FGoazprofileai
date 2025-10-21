from app import db
from app.models import Item, Audit
from config import Config
import json
from datetime import datetime

def seed_database():
    """Seed database with initial items if not already seeded."""
    if Item.query.count() > 0:
        return
    
    items_data = [
        {
            'stem': 'O que significa a sigla LLM no contexto de inteligência artificial?',
            'type': 'mcq',
            'competency': 'Fundamentos de IA/ML & LLMs',
            'difficulty_b': 0,
            'discrimination_a': 0.8,
            'choices': [
                'Large Language Model',
                'Linear Learning Machine',
                'Logical Language Mechanism',
                'Limited Learning Model'
            ],
            'answer_key': 'A',
            'tags': 'fundamentos,llm,conceitos'
        },
        {
            'stem': 'Qual das seguintes NÃO é uma característica dos modelos GPT?',
            'type': 'mcq',
            'competency': 'Fundamentos de IA/ML & LLMs',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Processamento de linguagem natural',
                'Geração de texto baseada em contexto',
                'Determinístico (sempre gera a mesma resposta)',
                'Treinamento com grandes volumes de dados'
            ],
            'answer_key': 'C',
            'tags': 'fundamentos,gpt,características'
        },
        {
            'stem': 'Explique brevemente o conceito de "fine-tuning" em modelos de IA.',
            'type': 'open_ended',
            'competency': 'Fundamentos de IA/ML & LLMs',
            'difficulty_b': 2,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Menciona ajuste de modelo pré-treinado',
                'precisao': 'Explica uso de dados específicos do domínio',
                'completude': 'Menciona melhoria de performance em tarefa específica'
            },
            'tags': 'fundamentos,fine-tuning,conceitos'
        },
        {
            'stem': 'Transformers revolucionaram o processamento de linguagem natural. Qual é o principal mecanismo que os diferencia?',
            'type': 'mcq',
            'competency': 'Fundamentos de IA/ML & LLMs',
            'difficulty_b': 2,
            'discrimination_a': 0.7,
            'choices': [
                'Redes neurais convolucionais',
                'Mecanismo de atenção (attention mechanism)',
                'Árvores de decisão',
                'Redes neurais recorrentes simples'
            ],
            'answer_key': 'B',
            'tags': 'fundamentos,transformers,arquitetura'
        },
        {
            'stem': 'Qual ferramenta de IA você usa com mais frequência no seu trabalho?',
            'type': 'mcq',
            'competency': 'Ferramentas de IA no dia a dia',
            'difficulty_b': 0,
            'discrimination_a': 0.5,
            'choices': [
                'ChatGPT ou Claude',
                'GitHub Copilot ou similar',
                'Ferramentas de geração de imagem (DALL-E, Midjourney)',
                'Ainda não uso ferramentas de IA regularmente'
            ],
            'answer_key': 'A',
            'tags': 'ferramentas,uso,cotidiano'
        },
        {
            'stem': 'Você precisa resumir 50 PDFs de pesquisa. Qual abordagem seria mais eficiente com IA?',
            'type': 'scenario',
            'competency': 'Ferramentas de IA no dia a dia',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Copiar e colar cada PDF no ChatGPT manualmente',
                'Usar uma ferramenta com processamento em lote (batch) e RAG',
                'Pedir para o ChatGPT "resumir 50 PDFs"',
                'Ler todos manualmente e depois pedir resumo'
            ],
            'answer_key': 'B',
            'tags': 'ferramentas,produtividade,rag'
        },
        {
            'stem': 'Descreva uma situação real em que você usou (ou usaria) IA para automatizar uma tarefa repetitiva.',
            'type': 'open_ended',
            'competency': 'Ferramentas de IA no dia a dia',
            'difficulty_b': 1,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Descreve tarefa repetitiva clara',
                'precisao': 'Menciona ferramenta ou abordagem específica',
                'completude': 'Explica benefício ou resultado'
            },
            'tags': 'ferramentas,automação,prática'
        },
        {
            'stem': 'Para integrar IA generativa em um produto, qual ferramenta oferece melhor controle de custos e latência?',
            'type': 'mcq',
            'competency': 'Ferramentas de IA no dia a dia',
            'difficulty_b': 2,
            'discrimination_a': 0.8,
            'choices': [
                'Usar apenas APIs públicas sem monitoramento',
                'Self-hosting de modelos open-source otimizados',
                'Sempre usar o modelo mais avançado disponível',
                'Evitar cache e sempre fazer novas requisições'
            ],
            'answer_key': 'B',
            'tags': 'ferramentas,custos,produção'
        },
        {
            'stem': 'Escreva um prompt para um LLM extrair os principais insights de um relatório de vendas trimestral.',
            'type': 'prompt_writing',
            'competency': 'Prompt Engineering & Orquestração',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'rubric': {
                'relevancia': 'Prompt direcionado para extração de insights',
                'precisao': 'Especifica formato de saída ou pontos-chave',
                'completude': 'Inclui contexto sobre o relatório',
                'objetividade': 'Claro e acionável'
            },
            'tags': 'prompt,engineering,prática'
        },
        {
            'stem': 'O que é "chain-of-thought prompting"?',
            'type': 'mcq',
            'competency': 'Prompt Engineering & Orquestração',
            'difficulty_b': 1,
            'discrimination_a': 0.8,
            'choices': [
                'Encadear múltiplas APIs em sequência',
                'Pedir ao modelo para raciocinar passo a passo',
                'Usar prompts muito longos',
                'Fazer perguntas em cadeia ao usuário'
            ],
            'answer_key': 'B',
            'tags': 'prompt,chain-of-thought,técnicas'
        },
        {
            'stem': 'Você quer que o LLM gere respostas em JSON estruturado. Qual técnica é mais eficaz?',
            'type': 'mcq',
            'competency': 'Prompt Engineering & Orquestração',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Apenas pedir "responda em JSON"',
                'Fornecer schema e exemplo no prompt',
                'Usar temperatura muito alta para criatividade',
                'Não especificar formato e parsear depois'
            ],
            'answer_key': 'B',
            'tags': 'prompt,json,estruturado'
        },
        {
            'stem': 'Explique o conceito de "orquestração de agentes" e dê um exemplo de uso.',
            'type': 'open_ended',
            'competency': 'Prompt Engineering & Orquestração',
            'difficulty_b': 2,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Define orquestração de múltiplos agentes',
                'precisao': 'Menciona coordenação ou frameworks',
                'completude': 'Fornece exemplo prático de caso de uso'
            },
            'tags': 'orquestração,agentes,conceitos'
        },
        {
            'stem': 'O que significa RAG (Retrieval-Augmented Generation)?',
            'type': 'mcq',
            'competency': 'Dados & Contextualização (RAG)',
            'difficulty_b': 0,
            'discrimination_a': 0.8,
            'choices': [
                'Recuperar informações de uma base antes de gerar resposta',
                'Gerar dados aleatórios para treinar modelos',
                'Revisar automaticamente a gramática de textos',
                'Reduzir o tamanho de arquivos grandes'
            ],
            'answer_key': 'A',
            'tags': 'rag,conceitos,fundamentos'
        },
        {
            'stem': 'Qual é o principal benefício de usar embeddings em sistemas RAG?',
            'type': 'mcq',
            'competency': 'Dados & Contextualização (RAG)',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Reduzir custos de armazenamento',
                'Busca semântica mais precisa do que keyword matching',
                'Aumentar a velocidade de escrita no banco',
                'Eliminar a necessidade de LLMs'
            ],
            'answer_key': 'B',
            'tags': 'rag,embeddings,busca'
        },
        {
            'stem': 'Você tem uma base com 10.000 documentos técnicos. Como implementaria um sistema de Q&A com RAG?',
            'type': 'scenario',
            'competency': 'Dados & Contextualização (RAG)',
            'difficulty_b': 2,
            'discrimination_a': 0.7,
            'choices': [
                'Enviar todos os 10k docs em cada prompt',
                'Criar embeddings, indexar em vector DB, recuperar top-k relevantes',
                'Usar apenas busca por palavras-chave no Google',
                'Treinar um modelo do zero com os documentos'
            ],
            'answer_key': 'B',
            'tags': 'rag,implementação,vectordb'
        },
        {
            'stem': 'Descreva estratégias para melhorar a qualidade das respostas em um sistema RAG.',
            'type': 'open_ended',
            'competency': 'Dados & Contextualização (RAG)',
            'difficulty_b': 2,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Menciona técnicas de melhoria de retrieval ou geração',
                'precisao': 'Cita métodos específicos (reranking, chunking, etc)',
                'completude': 'Aborda múltiplas dimensões do pipeline'
            },
            'tags': 'rag,qualidade,otimização'
        },
        {
            'stem': 'Qual processo empresarial é MAIS adequado para automação com IA generativa?',
            'type': 'mcq',
            'competency': 'Automação de Processos com IA',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Decisões estratégicas de alto risco sem supervisão',
                'Triagem e categorização de e-mails de suporte',
                'Cirurgias médicas autônomas',
                'Aprovação final de orçamentos corporativos'
            ],
            'answer_key': 'B',
            'tags': 'automação,processos,casos-de-uso'
        },
        {
            'stem': 'Você quer automatizar a geração de relatórios semanais. Qual abordagem é mais robusta?',
            'type': 'scenario',
            'competency': 'Automação de Processos com IA',
            'difficulty_b': 1,
            'discrimination_a': 0.6,
            'choices': [
                'Copiar e colar dados manualmente no ChatGPT toda semana',
                'Criar pipeline: extração de dados → LLM com template → revisão humana',
                'Deixar IA decidir sozinha o que incluir sem validação',
                'Fazer tudo manualmente para evitar erros'
            ],
            'answer_key': 'B',
            'tags': 'automação,pipeline,boas-práticas'
        },
        {
            'stem': 'Descreva um processo na sua área que poderia ser parcialmente automatizado com IA e como você o faria.',
            'type': 'open_ended',
            'competency': 'Automação de Processos com IA',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'rubric': {
                'relevancia': 'Identifica processo claro e viável',
                'precisao': 'Descreve etapas de automação',
                'completude': 'Considera validação humana ou riscos'
            },
            'tags': 'automação,prática,planejamento'
        },
        {
            'stem': 'Qual é o principal risco ao automatizar processos críticos exclusivamente com IA?',
            'type': 'mcq',
            'competency': 'Automação de Processos com IA',
            'difficulty_b': 2,
            'discrimination_a': 0.8,
            'choices': [
                'Economia de tempo',
                'Falta de supervisão humana em decisões importantes',
                'Redução de custos operacionais',
                'Aumento de eficiência'
            ],
            'answer_key': 'B',
            'tags': 'automação,riscos,governança'
        },
        {
            'stem': 'Por que é importante revisar outputs de IA antes de usar em contextos públicos ou sensíveis?',
            'type': 'mcq',
            'competency': 'Ética, Segurança & Compliance',
            'difficulty_b': 0,
            'discrimination_a': 0.9,
            'choices': [
                'IA pode gerar conteúdo incorreto, enviesado ou inadequado',
                'Para aumentar o custo do projeto',
                'Porque IA nunca erra',
                'Não é necessário revisar'
            ],
            'answer_key': 'A',
            'tags': 'ética,revisão,qualidade'
        },
        {
            'stem': 'Sua empresa quer usar IA para análise de CVs. Qual prática é essencial para evitar viés discriminatório?',
            'type': 'scenario',
            'competency': 'Ética, Segurança & Compliance',
            'difficulty_b': 1,
            'discrimination_a': 0.8,
            'choices': [
                'Usar IA sem nenhuma validação',
                'Auditar regularmente as decisões e remover atributos sensíveis (raça, gênero, idade)',
                'Confiar 100% nas recomendações da IA',
                'Usar apenas modelos treinados com dados antigos'
            ],
            'answer_key': 'B',
            'tags': 'ética,viés,rh'
        },
        {
            'stem': 'Você descobre que um prompt pode fazer o LLM vazar informações confidenciais. O que fazer?',
            'type': 'scenario',
            'competency': 'Ética, Segurança & Compliance',
            'difficulty_b': 2,
            'discrimination_a': 0.9,
            'choices': [
                'Ignorar o problema',
                'Reportar imediatamente e implementar filtros de segurança',
                'Compartilhar publicamente sem avisar a empresa',
                'Usar o prompt para benefício próprio'
            ],
            'answer_key': 'B',
            'tags': 'segurança,vazamento,compliance'
        },
        {
            'stem': 'Explique a importância da transparência ao usar IA em decisões que afetam pessoas (ex: crédito, contratação).',
            'type': 'open_ended',
            'competency': 'Ética, Segurança & Compliance',
            'difficulty_b': 2,
            'discrimination_a': 0.7,
            'rubric': {
                'relevancia': 'Aborda transparência e explicabilidade',
                'precisao': 'Menciona direitos ou regulamentação (LGPD, etc)',
                'completude': 'Explica impacto em confiança ou justiça'
            },
            'tags': 'ética,transparência,regulamentação'
        },
        {
            'stem': 'Ao desenvolver um produto com IA, qual pergunta de negócio é mais relevante?',
            'type': 'mcq',
            'competency': 'Produto e Negócio com IA',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Qual é o modelo de IA mais avançado disponível?',
                'Qual problema real do cliente estamos resolvendo?',
                'Quantos parâmetros tem o modelo?',
                'Qual linguagem de programação é mais moderna?'
            ],
            'answer_key': 'B',
            'tags': 'produto,negócio,estratégia'
        },
        {
            'stem': 'Como você mediria o ROI de uma iniciativa de IA em customer support?',
            'type': 'scenario',
            'competency': 'Produto e Negócio com IA',
            'difficulty_b': 2,
            'discrimination_a': 0.7,
            'choices': [
                'Contar número de modelos usados',
                'Medir redução de tempo de resposta, custos e satisfação do cliente',
                'Ver quantas linhas de código foram escritas',
                'Apenas observar se "parece melhor"'
            ],
            'answer_key': 'B',
            'tags': 'produto,roi,métricas'
        },
        {
            'stem': 'Descreva como você validaria se uma funcionalidade de IA agrega valor real antes de lançá-la.',
            'type': 'open_ended',
            'competency': 'Produto e Negócio com IA',
            'difficulty_b': 2,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Menciona testes com usuários ou métricas',
                'precisao': 'Descreve processo de validação estruturado',
                'completude': 'Considera feedback e iteração'
            },
            'tags': 'produto,validação,mvp'
        },
        {
            'stem': 'Qual métrica NÃO é relevante para avaliar o impacto de negócio de IA?',
            'type': 'mcq',
            'competency': 'Produto e Negócio com IA',
            'difficulty_b': 1,
            'discrimination_a': 0.8,
            'choices': [
                'Tempo de resposta médio',
                'Satisfação do usuário (NPS/CSAT)',
                'Número de neurônios na rede',
                'Redução de custos operacionais'
            ],
            'answer_key': 'C',
            'tags': 'produto,métricas,negócio'
        },
        {
            'stem': 'Qual plataforma no-code/low-code permite criar workflows com IA generativa facilmente?',
            'type': 'mcq',
            'competency': 'Code/No-code para IA',
            'difficulty_b': 1,
            'discrimination_a': 0.6,
            'choices': [
                'Zapier com integração OpenAI',
                'Microsoft Excel sem plugins',
                'Bloco de notas',
                'Paint'
            ],
            'answer_key': 'A',
            'tags': 'nocode,ferramentas,automação'
        },
        {
            'stem': 'Você quer prototipar um chatbot sem programar. Qual abordagem é viável?',
            'type': 'scenario',
            'competency': 'Code/No-code para IA',
            'difficulty_b': 1,
            'discrimination_a': 0.7,
            'choices': [
                'Usar plataformas como Voiceflow ou Botpress',
                'Escrever tudo em Assembly',
                'Apenas sonhar com o chatbot',
                'Esperar alguém fazer para você'
            ],
            'answer_key': 'A',
            'tags': 'nocode,chatbot,prototipagem'
        },
        {
            'stem': 'Descreva uma situação onde usar no-code para IA seria mais eficiente do que desenvolver código do zero.',
            'type': 'open_ended',
            'competency': 'Code/No-code para IA',
            'difficulty_b': 1,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Identifica caso de uso apropriado',
                'precisao': 'Justifica eficiência (tempo, recursos)',
                'completude': 'Compara com desenvolvimento tradicional'
            },
            'tags': 'nocode,eficiência,casos-de-uso'
        },
        {
            'stem': 'Qual é uma limitação comum de ferramentas no-code para IA?',
            'type': 'mcq',
            'competency': 'Code/No-code para IA',
            'difficulty_b': 2,
            'discrimination_a': 0.8,
            'choices': [
                'São sempre gratuitas',
                'Customização limitada para casos muito específicos',
                'Funcionam offline sem internet',
                'Não precisam de dados'
            ],
            'answer_key': 'B',
            'tags': 'nocode,limitações,trade-offs'
        },
        {
            'stem': 'O que significa "LLMOps"?',
            'type': 'mcq',
            'competency': 'LLMOps & Qualidade',
            'difficulty_b': 1,
            'discrimination_a': 0.8,
            'choices': [
                'Operacionalização e gestão de Large Language Models',
                'Linguagem de programação para IA',
                'Sistema operacional para servidores',
                'Limpeza de dados'
            ],
            'answer_key': 'A',
            'tags': 'llmops,conceitos,operações'
        },
        {
            'stem': 'Qual prática é fundamental em LLMOps para garantir qualidade contínua?',
            'type': 'mcq',
            'competency': 'LLMOps & Qualidade',
            'difficulty_b': 2,
            'discrimination_a': 0.7,
            'choices': [
                'Nunca monitorar outputs após deploy',
                'Implementar logging, monitoring e evaluation loops',
                'Usar sempre o mesmo prompt sem testar',
                'Ignorar feedback dos usuários'
            ],
            'answer_key': 'B',
            'tags': 'llmops,monitoramento,qualidade'
        },
        {
            'stem': 'Você detecta degradação na qualidade das respostas do seu LLM em produção. O que fazer?',
            'type': 'scenario',
            'competency': 'LLMOps & Qualidade',
            'difficulty_b': 2,
            'discrimination_a': 0.8,
            'choices': [
                'Ignorar e esperar melhorar sozinho',
                'Investigar logs, analisar exemplos ruins, ajustar prompts ou modelo',
                'Desligar o sistema imediatamente',
                'Culpar os usuários'
            ],
            'answer_key': 'B',
            'tags': 'llmops,troubleshooting,produção'
        },
        {
            'stem': 'Explique a importância de versionar prompts e manter histórico de mudanças em sistemas de IA.',
            'type': 'open_ended',
            'competency': 'LLMOps & Qualidade',
            'difficulty_b': 2,
            'discrimination_a': 0.6,
            'rubric': {
                'relevancia': 'Aborda controle de versão e rastreabilidade',
                'precisao': 'Menciona debugging ou rollback',
                'completude': 'Explica impacto em qualidade ou confiabilidade'
            },
            'tags': 'llmops,versionamento,governança'
        }
    ]
    
    for item_data in items_data:
        item = Item(
            stem=item_data['stem'],
            type=item_data['type'],
            competency=item_data['competency'],
            difficulty_b=item_data['difficulty_b'],
            discrimination_a=item_data['discrimination_a'],
            tags=item_data.get('tags', ''),
            active=True
        )
        
        if 'choices' in item_data:
            item.choices = item_data['choices']
        if 'answer_key' in item_data:
            item.answer_key = item_data['answer_key']
        if 'rubric' in item_data:
            item.rubric = item_data['rubric']
        
        db.session.add(item)
    
    db.session.commit()
    
    audit = Audit(
        actor='system',
        action='seed_database',
        target='items',
        payload={'count': len(items_data), 'timestamp': datetime.utcnow().isoformat()}
    )
    db.session.add(audit)
    db.session.commit()

def log_audit(actor: str, action: str, target: str, payload: dict = None):
    """Log an audit entry."""
    audit = Audit(
        actor=actor,
        action=action,
        target=target,
        payload=payload or {}
    )
    db.session.add(audit)
    db.session.commit()
