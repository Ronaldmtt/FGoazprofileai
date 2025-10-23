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
    
    def generate_matrix_question(
        self,
        block_name: str,
        response_history: list = None,
        user_context: dict = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized question for the Matrix assessment.
        
        Args:
            block_name: One of 4 blocks (Percepção, Uso Prático, Conhecimento, Cultura)
            response_history: Previous responses for context
            user_context: User info (name, department, role) for personalization
            
        Returns:
            Dict with question data ready to be saved as Item
        """
        from app.core.blocks_config import BLOCKS
        
        logger.info(f"Generating matrix question for block: {block_name}")
        
        if not user_context:
            user_context = {'name': 'Usuário', 'department': 'Geral', 'role': 'Profissional'}
        
        # Get block configuration
        block_config = BLOCKS.get(block_name, {})
        block_description = block_config.get('description', '')
        block_examples = block_config.get('examples', [])
        
        # Build context from history
        context_str = f"\n**Perfil do Usuário**:\n- Nome: {user_context['name']}\n- Área: {user_context['department']}\n- Cargo: {user_context['role']}\n"
        
        # Add previously asked questions to AVOID REPETITION
        previous_questions = []
        if response_history:
            for resp in response_history[-5:]:  # Last 5 questions
                if 'stem' in resp:
                    previous_questions.append(resp['stem'])
        
        if previous_questions:
            context_str += f"\n**IMPORTANTE - NÃO REPITA estas perguntas já feitas**:\n"
            for i, q in enumerate(previous_questions, 1):
                context_str += f"{i}. {q}\n"
            context_str += "\n**Você DEVE criar uma pergunta DIFERENTE das acima!**\n"
        
        # Show example questions from this block
        examples_str = "\n**Exemplos de perguntas deste bloco**:\n"
        for example in block_examples[:2]:
            examples_str += f"- {example}\n"
        
        prompt = f"""Você é um especialista em criar questionários de maturidade em IA para ambientes corporativos.

**CONTEXTO DA AVALIAÇÃO**:
- Empresa: OAZ
- Bloco sendo avaliado: **{block_name}** - {block_description}
- Cargo do usuário: {user_context['role']}
- Área: {user_context['department']}

{context_str}

{examples_str}

**FORMATO OBRIGATÓRIO - MATRIZ DE 4 ALTERNATIVAS PROGRESSIVAS**:

As 4 alternativas devem representar níveis crescentes de maturidade em IA, do menos ao mais experiente:
- **Opção A**: Iniciante - nunca usou, não conhece, vê como distante
- **Opção B**: Explorador - já testou, tem noção básica, curioso  
- **Opção C**: Praticante - usa regularmente, entende conceitos, integra ao trabalho
- **Opção D**: Líder Digital - domina, ensina outros, influencia, automatiza

**REGRAS CRÍTICAS**:

1. **Progressão natural e realista**:
   - Cada opção deve ser plausível e verdadeira para alguém naquele nível
   - NÃO crie opções absurdas ou obviamente erradas
   - Todas as 4 opções devem fazer sentido em contextos diferentes

2. **Evite pistas óbvias**:
   - Comprimento similar entre opções (±30%)
   - Linguagem consistente
   - Não use sempre/nunca de forma óbvia
   - Varie a posição da resposta mais avançada

3. **Personalização ao contexto do usuário**:
   - Use termos da área {user_context['department']}
   - Exemplos relevantes ao cargo {user_context['role']}
   - Situações práticas do dia a dia

4. **IMPORTANTE - NÃO REVELE O SISTEMA DE PONTUAÇÃO**:
   - NÃO inclua pontos (ex: "1 pt", "2 pontos") nas alternativas
   - NÃO inclua níveis (ex: "Iniciante", "Explorador") nas alternativas
   - As alternativas devem conter APENAS o texto descritivo da opção
   - O usuário NÃO deve saber qual alternativa vale mais pontos

**EXEMPLO DE BOA PERGUNTA**:

Pergunta: "Com que frequência você usa ferramentas de IA (ChatGPT, Copilot, etc.) no seu trabalho?"

A) Nunca usei ou testei apenas por curiosidade
B) Uso ocasionalmente para algumas tarefas específicas
C) Uso frequentemente e integrei nos meus fluxos de trabalho
D) Uso diariamente, automatizo processos e ensino outros colegas

**RETORNE JSON (SEM PONTOS OU NÍVEIS NAS ALTERNATIVAS)**:
{{
  "stem": "Pergunta clara e direta relacionada ao bloco '{block_name}'",
  "choices": [
    "Nunca considerei ou não vejo relevância",
    "Já ouvi falar e tenho curiosidade de testar",
    "Uso regularmente e vejo benefícios claros",
    "Domino completamente e ajudo outros a usar"
  ],
  "progressive_levels": true,
  "block": "{block_name}"
}}

LEMBRE-SE: Esta não é uma prova com "certas" e "erradas". É uma avaliação de maturidade onde cada pessoa escolhe a opção que MELHOR REFLETE sua realidade atual! **NUNCA inclua pontos ou classificações de nível nas alternativas mostradas ao usuário.**"""

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
            
            # Build complete item data for matrix format
            return {
                'stem': question_data.get('stem', 'Questão gerada'),
                'type': 'matrix',  # New type for matrix questions
                'block': block_name,  # Changed from 'competency' to 'block'
                'choices': question_data.get('choices', []),
                'progressive_levels': True,  # Mark as progressive (A=1, B=2, C=3, D=4)
                'tags': f'generated,matrix,{block_config.get("id", "unknown")}',
                'metadata': {
                    'generated': True,
                    'block_description': block_description,
                    'user_context': user_context
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
