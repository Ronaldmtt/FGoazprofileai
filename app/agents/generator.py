from typing import Dict, Any
import json
from app.core.llm_provider import LLMProvider
from app.models import Item
import logging

logger = logging.getLogger(__name__)

class AgentGenerator:
    """
    Generates personalized questions dynamically based on user proficiency level.
    Uses OpenAI to create contextual, adaptive questions.
    """
    
    def __init__(self):
        # Use OpenAI for intelligent question generation
        self.llm = LLMProvider('openai')
    
    def generate_adaptive_question(
        self,
        competency: str,
        current_score: float,
        difficulty_target: str,
        response_history: list = None,
        user_context: dict = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized question adapted to user's current level.
        
        Args:
            competency: AI competency area (e.g., "Fundamentos de IA/ML & LLMs")
            current_score: User's current proficiency score (0-100)
            difficulty_target: 'easy', 'medium', or 'hard'
            response_history: Previous responses for context
            user_context: User info (name, department, role) for personalization
            
        Returns:
            Dict with question data ready to be saved as Item
        """
        logger.info(f"Generating adaptive question for {competency} at level {difficulty_target}")
        
        if not user_context:
            user_context = {'name': 'Usuário', 'department': 'Geral', 'role': 'Profissional'}
        
        # Map difficulty to IRT parameters (theta scale: -3 to +3)
        difficulty_map = {
            'easy': {'b': -1.0, 'a': 1.2, 'description': 'básico/introdutório'},
            'medium': {'b': 0.0, 'a': 1.5, 'description': 'intermediário/prático'},
            'hard': {'b': 1.5, 'a': 1.8, 'description': 'avançado/especialista'}
        }
        
        diff_params = difficulty_map.get(difficulty_target, difficulty_map['medium'])
        
        # Build context from history
        context_str = f"\n**Perfil do Usuário**:\n- Nome: {user_context['name']}\n- Área: {user_context['department']}\n- Cargo: {user_context['role']}\n"
        
        if response_history:
            recent = response_history[-3:]  # Last 3 responses
            context_str += "\n**Respostas anteriores**:\n"
            for resp in recent:
                context_str += f"- {resp.get('competency')}: pontuou {resp.get('score', 0):.1f}\n"
        
        # Choose question format randomly for variety
        import random
        format_type = random.choice(['scenario', 'technical', 'comparison', 'debugging', 'trade-off'])
        
        format_instructions = {
            'scenario': f"CENÁRIO PRÁTICO: {user_context['role']} precisa resolver problema real de {competency}",
            'technical': f"CONHECIMENTO TÉCNICO: Teste entendimento profundo de como funcionam algoritmos/técnicas de {competency}",
            'comparison': f"COMPARAÇÃO: Escolher entre abordagens diferentes para problema específico de {competency}",
            'debugging': f"DEBUGGING: Identificar problema ou melhorar implementação existente relacionada a {competency}",
            'trade-off': f"TRADE-OFFS: Avaliar prós/contras de decisões técnicas em contexto de {competency}"
        }
        
        prompt = f"""Você é especialista em avaliação TÉCNICA de IA. Gere questão DESAFIADORA formato: **{format_type.upper()}**

**Competência**: {competency}
**Nível usuário**: {current_score:.0f}/100
**Dificuldade**: {diff_params['description']}
**Contexto**: {user_context['role']} em {user_context['department']}
{context_str}

**TIPO DE QUESTÃO**: {format_instructions[format_type]}

REQUISITOS OBRIGATÓRIOS:
1. VARIE o tipo de pergunta - não repita sempre "Victor deseja implementar..."
2. TESTE conhecimento TÉCNICO específico: 
   - Parâmetros de modelos e como ajustá-los
   - Trade-offs entre técnicas (acurácia vs interpretabilidade, custo vs performance)
   - Quando usar supervised vs unsupervised vs reinforcement learning
   - Limitações de cada abordagem
   - Debugging e otimização de modelos
3. 4 alternativas TÉCNICAS (não genéricas) - todas plausíveis
4. Contextualize no trabalho de {user_context['role']} mas FOQUE em AI/ML
5. Se dificuldade=avançado: inclua hiperparâmetros, métricas, arquiteturas específicas

FORMATOS VARIADOS:
- "Dado dataset X com características Y, qual arquitetura/técnica é mais apropriada?"
- "Modelo apresenta problema Z, qual é a causa MAIS provável e solução?"
- "Entre técnicas A, B, C, D para objetivo X, qual melhor considerando constraints Y?"
- "Para melhorar métrica X mantendo Y, qual ajuste fazer?"
- "Código/implementação tem issue X, qual correção?"

NÃO FAZER:
❌ Sempre começar "Victor/João deseja implementar..."
❌ Perguntas genéricas sobre ética sem aspecto técnico
❌ Definições básicas ("O que é machine learning?")
❌ Perguntas de senso comum

RETORNE JSON:
{{
  "stem": "Pergunta técnica direta e específica (varie formato!)",
  "choices": ["A) Solução técnica específica", "B) Outra abordagem técnica", "C) Alternativa técnica", "D) Mais uma opção técnica"],
  "answer_key": "A/B/C/D",
  "explanation": "Justificativa técnica detalhada",
  "rubric_criteria": {{"profundidade_tecnica": "entendimento conceitos", "aplicacao": "usar corretamente"}}
}}

SEJA TÉCNICO E VARIADO!"""

        try:
            # Skip if LLM provider is stub
            if self.llm.provider == 'stub' or not self.llm.client:
                logger.warning("[ADAPTIVE] OpenAI not available, skipping generation")
                return None
            
            logger.info(f"[ADAPTIVE] Calling OpenAI for user {user_context['name']} ({user_context['role']} - {user_context['department']})")
            
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um gerador de questões técnicas para avaliação de proficiência em IA. Seja preciso, técnico e contextualizado."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=600
            )
            
            # Log response for debugging
            logger.info(f"[ADAPTIVE] OpenAI response object: {response}")
            logger.info(f"[ADAPTIVE] Response choices: {response.choices}")
            
            message = response.choices[0].message
            raw_content = message.content
            
            # Check for refusal
            if hasattr(message, 'refusal') and message.refusal:
                logger.error(f"[ADAPTIVE] OpenAI REFUSED to generate: {message.refusal}")
                return None
            
            logger.info(f"[ADAPTIVE] OpenAI raw response (first 200 chars): {raw_content[:200] if raw_content else 'EMPTY/NONE'}")
            
            if not raw_content:
                logger.error("[ADAPTIVE] OpenAI returned empty content!")
                return None
            
            question_data = json.loads(raw_content)
            
            # Build complete item data
            return {
                'stem': question_data.get('stem', 'Questão gerada'),
                'type': 'mcq',
                'competency': competency,
                'difficulty_b': diff_params['b'],
                'discrimination_a': diff_params['a'],
                'choices': question_data.get('choices', []),
                'answer_key': question_data.get('answer_key', 'A'),
                'rubric': question_data.get('rubric_criteria', {}),
                'tags': f'generated,adaptive,{difficulty_target}',
                'metadata': {
                    'generated': True,
                    'target_score': current_score,
                    'explanation': question_data.get('explanation', '')
                }
            }
            
        except Exception as e:
            logger.error(f"[ADAPTIVE] ERROR generating question: {e}")
            # Return None - NO fallback to generic questions
            return None
    
    def generate_variation(self, original_item: Dict[str, Any]) -> Dict[str, Any]:
        """Generate variation of an existing item."""
        prompt = f"Create a variation of this question: {original_item.get('stem')}"
        variation = self.llm.generate(prompt, {'original': original_item})
        
        return {
            'stem': variation,
            'type': original_item['type'],
            'competency': original_item['competency'],
            'difficulty_b': original_item.get('difficulty_b', 1.0),
            'discrimination_a': original_item.get('discrimination_a', 0.5)
        }
    
    def validate_language(self, text: str) -> Dict[str, Any]:
        """Validate question language for clarity and appropriateness."""
        moderation = self.llm.moderate(text)
        
        is_clear = len(text) > 10 and len(text) < 1000
        
        return {
            'valid': moderation['safe'] and is_clear,
            'issues': moderation.get('flags', []),
            'suggestions': []
        }
