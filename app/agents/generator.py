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
        response_history: list = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized question adapted to user's current level.
        
        Args:
            competency: AI competency area (e.g., "Fundamentos de IA/ML & LLMs")
            current_score: User's current proficiency score (0-100)
            difficulty_target: 'easy', 'medium', or 'hard'
            response_history: Previous responses for context
            
        Returns:
            Dict with question data ready to be saved as Item
        """
        logger.info(f"Generating adaptive question for {competency} at level {difficulty_target}")
        
        # Map difficulty to parameters
        difficulty_map = {
            'easy': {'b': 0, 'a': 0.6, 'description': 'básico/introdutório'},
            'medium': {'b': 1, 'a': 0.7, 'description': 'intermediário/prático'},
            'hard': {'b': 2, 'a': 0.9, 'description': 'avançado/especialista'}
        }
        
        diff_params = difficulty_map.get(difficulty_target, difficulty_map['medium'])
        
        # Build context from history
        context_str = ""
        if response_history:
            recent = response_history[-3:]  # Last 3 responses
            context_str = "\nContexto do usuário:\n"
            for resp in recent:
                context_str += f"- {resp.get('competency')}: pontuou {resp.get('score', 0):.1f}\n"
        
        prompt = f"""Você é um especialista em avaliação de proficiência em IA.

Gere UMA questão de múltipla escolha ({diff_params['description']}) sobre:
**Competência**: {competency}
**Nível do usuário**: {current_score:.0f}/100
**Dificuldade alvo**: {diff_params['description']}
{context_str}

REQUISITOS DA QUESTÃO:
1. Relevante para profissionais usando IA no trabalho
2. Baseada em cenários reais e práticos
3. Teste conhecimento aplicado, não decoreba
4. 4 alternativas plausíveis (A, B, C, D)
5. Uma resposta claramente correta

RETORNE JSON:
{{
  "stem": "texto da questão (contextualizada, prática, específica)",
  "choices": ["A...", "B...", "C...", "D..."],
  "answer_key": "A|B|C|D",
  "explanation": "breve justificativa da resposta correta",
  "rubric_criteria": {{"relevancia": "...", "precisao": "..."}}
}}

NÃO repita questões genéricas. Seja criativo e contextual."""

        try:
            # Skip if LLM provider is stub
            if self.llm.provider == 'stub' or not self.llm.client:
                logger.warning("OpenAI not available, skipping adaptive generation")
                return None
            
            response = self.llm.client.chat.completions.create(
                model="gpt-5",
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
                max_tokens=600
            )
            
            question_data = json.loads(response.choices[0].message.content)
            
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
            logger.error(f"Error generating adaptive question: {e}")
            # Fallback to fetching from database
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
