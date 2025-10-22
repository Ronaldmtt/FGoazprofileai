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
        
        # Map difficulty to parameters
        difficulty_map = {
            'easy': {'b': 0, 'a': 0.6, 'description': 'básico/introdutório'},
            'medium': {'b': 1, 'a': 0.7, 'description': 'intermediário/prático'},
            'hard': {'b': 2, 'a': 0.9, 'description': 'avançado/especialista'}
        }
        
        diff_params = difficulty_map.get(difficulty_target, difficulty_map['medium'])
        
        # Build context from history
        context_str = f"\n**Perfil do Usuário**:\n- Nome: {user_context['name']}\n- Área: {user_context['department']}\n- Cargo: {user_context['role']}\n"
        
        if response_history:
            recent = response_history[-3:]  # Last 3 responses
            context_str += "\n**Respostas anteriores**:\n"
            for resp in recent:
                context_str += f"- {resp.get('competency')}: pontuou {resp.get('score', 0):.1f}\n"
        
        prompt = f"""Você é um especialista em avaliação TÉCNICA de proficiência em IA.

Gere UMA questão de múltipla escolha ({diff_params['description']}) sobre:
**Competência**: {competency}
**Nível atual**: {current_score:.0f}/100
**Dificuldade alvo**: {diff_params['description']}
{context_str}

CRÍTICO - REQUISITOS DA QUESTÃO:
1. **PERSONALIZE para {user_context['role']} em {user_context['department']}** - use cenário real do trabalho deles
2. **TESTE CONHECIMENTO TÉCNICO REAL** - não faça perguntas óbvias ou de senso comum
3. Exija que o usuário demonstre ENTENDIMENTO PROFUNDO de conceitos de IA:
   - Como funcionam algoritmos/modelos
   - Quando usar cada técnica
   - Limitações e trade-offs
   - Aplicação prática correta
4. 4 alternativas desafiadoras (todas plausíveis, mas apenas 1 correta)
5. Evite perguntas genéricas sobre "ética" ou "compliance" - foque em CONHECIMENTO TÉCNICO

EXEMPLOS DO QUE FAZER:
✅ "Para prever churn de clientes com histórico de 6 meses, qual modelo seria mais eficaz considerando interpretabilidade e acurácia?"
✅ "Ao usar GPT-4 para análise de sentimento, qual técnica de prompt engineering reduziria viés nos resultados?"
✅ "Para automatizar classificação de tickets com 50 categorias e poucos exemplos por categoria, qual abordagem é mais adequada?"

EXEMPLOS DO QUE NÃO FAZER:
❌ "Qual a importância da ética em IA?" (muito genérico)
❌ "O que é machine learning?" (decoreba básico)
❌ Cenários longos sobre dilemas éticos sem testar conhecimento técnico

RETORNE JSON:
{{
  "stem": "Cenário específico do trabalho de {user_context['role']} que TESTE conhecimento técnico real",
  "choices": ["A) Solução técnica 1...", "B) Solução técnica 2...", "C) Solução técnica 3...", "D) Solução técnica 4..."],
  "answer_key": "A|B|C|D",
  "explanation": "Por que a resposta está correta tecnicamente",
  "rubric_criteria": {{"conhecimento_tecnico": "avalia profundidade", "aplicacao_pratica": "avalia uso correto"}}
}}

Seja DESAFIADOR. Teste se a pessoa realmente ENTENDE IA, não apenas ouviu falar."""

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
