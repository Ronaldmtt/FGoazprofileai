"""
Configuração dos 4 Blocos Temáticos do OAZ IA Profiler - Matriz Simplificada

Sistema de avaliação em 4 blocos com pontuação simples (1-4 por questão).
"""

# 4 Blocos Temáticos (substituem as 9 competências anteriores)
BLOCKS = {
    "Percepção e Atitude": {
        "id": "percepcao",
        "emoji": "🧭",
        "description": "Avalia o quanto a pessoa compreende e se posiciona diante da IA",
        "question_count": 3,
        "examples": [
            "Quando você ouve falar em 'Inteligência Artificial', o que vem à sua cabeça primeiro?",
            "Como você definiria o papel da IA no futuro da sua profissão?",
            "Qual sua opinião sobre o impacto da IA no mercado de trabalho?"
        ]
    },
    "Uso Prático": {
        "id": "uso_pratico",
        "emoji": "🧰",
        "description": "Avalia o nível de aplicação real no dia a dia de trabalho",
        "question_count": 3,
        "examples": [
            "Com que frequência você usa ferramentas de IA (ChatGPT, Copilot, Claude, etc.)?",
            "Para quais tipos de atividades você já usou IA?",
            "Quando você usa IA, o que normalmente faz?"
        ]
    },
    "Conhecimento e Entendimento": {
        "id": "conhecimento",
        "emoji": "🧠",
        "description": "Mede o nível de consciência técnica e conceitual",
        "question_count": 2,
        "examples": [
            "Você sabe o que é um modelo de linguagem (LLM)?",
            "Você entende a diferença entre IA generativa e IA preditiva?",
            "Quando você lê notícias sobre IA, o que costuma fazer?"
        ]
    },
    "Cultura e Autonomia Digital": {
        "id": "cultura",
        "emoji": "🚀",
        "description": "Mede a mentalidade de aprendizado e adaptação tecnológica",
        "question_count": 2,
        "examples": [
            "Se amanhã surgisse uma nova ferramenta de IA útil para sua área, você...",
            "Como você se sente em relação à IA no seu trabalho?"
        ]
    }
}

# Total de questões: 3 + 3 + 2 + 2 = 10 questões
TOTAL_QUESTIONS = sum(block["question_count"] for block in BLOCKS.values())

# Sistema de pontuação simples (sem IRT)
SCORING = {
    "points_per_question": {
        "a": 1,  # Iniciante/Nunca
        "b": 2,  # Explorador/Às vezes
        "c": 3,  # Praticante/Frequente
        "d": 4   # Líder/Sempre
    },
    "min_score": 10,   # 10 questões × 1 ponto
    "max_score": 40,   # 10 questões × 4 pontos
}

# 4 Níveis de Maturidade (substituem N0-N5)
MATURITY_LEVELS = {
    "Iniciante": {
        "range": (10, 17),
        "min_score": 10,
        "max_score": 17,
        "display_name": "Iniciante",
        "emoji": "🌱",
        "color": "#E5E7EB",
        "description": "Conhece superficialmente, pouco uso prático",
        "characteristics": [
            "Nunca ou raramente usa ferramentas de IA",
            "Não conhece conceitos básicos",
            "Vê IA como algo distante ou complexo",
            "Precisa de treinamento introdutório"
        ],
        "recommendations": [
            "Curso de Introdução à IA para Profissionais",
            "Workshop: Primeiros Passos com ChatGPT",
            "Tutoriais práticos de ferramentas básicas"
        ]
    },
    "Explorador": {
        "range": (18, 27),
        "min_score": 18,
        "max_score": 27,
        "display_name": "Explorador",
        "emoji": "🔍",
        "color": "#DBEAFE",
        "description": "Testa ferramentas, entende potencial",
        "characteristics": [
            "Já testou ferramentas de IA por curiosidade",
            "Entende alguns conceitos básicos",
            "Vê potencial mas não integrou à rotina",
            "Precisa de exemplos práticos aplicados"
        ],
        "recommendations": [
            "Curso: IA Aplicada ao Seu Trabalho",
            "Workshop: Prompt Engineering Prático",
            "Comunidade de Práticas de IA"
        ]
    },
    "Praticante": {
        "range": (28, 35),
        "min_score": 28,
        "max_score": 35,
        "display_name": "Praticante",
        "emoji": "⚡",
        "color": "#D1FAE5",
        "description": "Usa no trabalho, entende conceitos-chave",
        "characteristics": [
            "Usa IA regularmente no trabalho",
            "Conhece conceitos principais",
            "Integra ferramentas aos fluxos de trabalho",
            "Precisa de técnicas avançadas e automação"
        ],
        "recommendations": [
            "Curso Avançado: Automação com IA",
            "Workshop: LLMOps e Integração de APIs",
            "Certificação em IA Aplicada"
        ]
    },
    "Líder Digital": {
        "range": (36, 40),
        "min_score": 36,
        "max_score": 40,
        "display_name": "Líder Digital",
        "emoji": "🏆",
        "color": "#FDE68A",
        "description": "Integra, ensina e influencia o uso de IA",
        "characteristics": [
            "Domina múltiplas ferramentas de IA",
            "Cria automações e integrações",
            "Ensina e influencia outros colaboradores",
            "Referência em inovação com IA"
        ],
        "recommendations": [
            "Programa de Embaixadores de IA",
            "Mentoria para outros times",
            "Projetos de Inovação e R&D"
        ]
    }
}

def get_block_by_id(block_id: str):
    """Retorna configuração de um bloco pelo ID."""
    for name, config in BLOCKS.items():
        if config["id"] == block_id:
            return {**config, "name": name}
    return None

def get_level_by_score(total_score: int):
    """Retorna nível de maturidade baseado na pontuação total."""
    for level_name, level_config in MATURITY_LEVELS.items():
        min_score, max_score = level_config["range"]
        if min_score <= total_score <= max_score:
            return {**level_config, "name": level_name}
    
    # Fallback
    return {**MATURITY_LEVELS["Iniciante"], "name": "Iniciante"}

def calculate_total_score(responses: list) -> int:
    """
    Calcula pontuação total simples (soma de pontos).
    
    Args:
        responses: Lista de respostas com 'answer' (a/b/c/d)
    
    Returns:
        Pontuação total (10-40)
    """
    total = 0
    for response in responses:
        answer = response.get('answer', 'a').lower()
        points = SCORING["points_per_question"].get(answer, 1)
        total += points
    
    return total

def get_block_score(responses: list, block_name: str) -> dict:
    """
    Calcula pontuação de um bloco específico.
    
    Returns:
        Dict com score, percentage, questões respondidas
    """
    block_responses = [r for r in responses if r.get('block') == block_name]
    
    if not block_responses:
        return {
            "score": 0,
            "max_score": BLOCKS[block_name]["question_count"] * 4,
            "percentage": 0,
            "count": 0
        }
    
    score = sum(SCORING["points_per_question"].get(r.get('answer', 'a').lower(), 1) 
                for r in block_responses)
    max_score = len(block_responses) * 4
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": (score / max_score * 100) if max_score > 0 else 0,
        "count": len(block_responses)
    }
