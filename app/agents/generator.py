from typing import Dict, Any
import json
import random
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
        Generate a MACRO (transversal) question for Phase 1 assessment.
        
        Questions are NOT personalized by role/department - they measure universal
        competencies applicable to all professionals (conceptual understanding,
        logical reasoning, information-seeking behavior).
        
        Args:
            block_name: One of 4 blocks (Percepção, Uso Prático, Conhecimento, Cultura)
            response_history: Previous responses for context (avoid repetition)
            user_context: User info (name only for UX, NOT used in question generation)
            
        Returns:
            Dict with question data ready to be saved as Item
        """
        from app.core.blocks_config import BLOCKS
        
        logger.info(f"Generating MACRO (transversal) question for block: {block_name}")
        
        if not user_context:
            user_context = {'name': 'Usuário'}
        
        # Get block configuration
        block_config = BLOCKS.get(block_name, {})
        block_description = block_config.get('description', '')
        block_examples = block_config.get('examples', [])
        
        # Build context (MACRO: no role/department, only deduplication)
        context_str = ""
        
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
        
        prompt = f"""Você é um especialista em criar questionários de maturidade em IA para avaliação MACRO (transversal).

**CONTEXTO DA AVALIAÇÃO - FASE 1 (MACRO)**:
Esta é uma avaliação GERAL E TRANSVERSAL que mede competências universais aplicáveis a TODOS os profissionais, independente de área ou cargo.

- Empresa: OAZ
- Bloco sendo avaliado: **{block_name}** - {block_description}
- Tipo de avaliação: **MACRO (transversal)** - NÃO personalizar por área/cargo

{context_str}

{examples_str}

**COMPETÊNCIAS MACRO QUE ESTAMOS MEDINDO**:
1. **Compreensão Conceitual**: O que é IA e como se aplica ao trabalho (de forma ampla, não específica)
2. **Raciocínio Lógico/Analítico**: Capacidade de identificar situações onde IA pode resolver problemas
3. **Capacidade de Pesquisa/Interpretação**: Esforço para buscar e aplicar conhecimento sobre IA

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

3. **ABORDAGEM MACRO (CRÍTICO)**:
   - Perguntas devem ser GENÉRICAS e aplicáveis a QUALQUER profissional
   - NÃO mencione áreas específicas (marketing, RH, tecnologia, jurídico, etc.)
   - NÃO mencione cargos específicos (gerente, analista, diretor, etc.)
   - Use linguagem universal: "no seu trabalho", "nas suas atividades", "na sua rotina"
   - Foco em COMPETÊNCIAS TRANSVERSAIS, não habilidades técnicas de área

4. **IMPORTANTE - NÃO REVELE O SISTEMA DE PONTUAÇÃO**:
   - NÃO inclua pontos (ex: "1 pt", "2 pontos") nas alternativas
   - NÃO inclua níveis (ex: "Iniciante", "Explorador") nas alternativas
   - As alternativas devem conter APENAS o texto descritivo da opção
   - O usuário NÃO deve saber qual alternativa vale mais pontos

**EXEMPLO DE BOA PERGUNTA MACRO (TRANSVERSAL)**:

❌ RUIM (específico de área): "Como você usa IA para criar campanhas de marketing?"
✅ BOM (macro/universal): "Com que frequência você usa ferramentas de IA no seu trabalho?"

❌ RUIM (menciona cargo): "Como gerente, você incentiva o uso de IA?"
✅ BOM (macro/universal): "Você costuma compartilhar conhecimentos sobre IA com colegas?"

**PERGUNTA EXEMPLO**:
Pergunta: "Com que frequência você usa ferramentas de IA (ChatGPT, Copilot, etc.) no seu trabalho?"

A) Nunca usei ou testei apenas por curiosidade
B) Uso ocasionalmente para algumas tarefas específicas
C) Uso frequentemente e integrei nos meus fluxos de trabalho
D) Uso diariamente, automatizo processos e ensino outros colegas

**RETORNE JSON (SEM PONTOS OU NÍVEIS NAS ALTERNATIVAS)**:
{{
  "stem": "Pergunta MACRO (transversal) relacionada ao bloco '{block_name}' - aplicável a QUALQUER profissional",
  "choices": [
    "Nunca considerei ou não vejo relevância",
    "Já ouvi falar e tenho curiosidade de testar",
    "Uso regularmente e vejo benefícios claros",
    "Domino completamente e ajudo outros a usar"
  ],
  "progressive_levels": true,
  "block": "{block_name}"
}}

LEMBRE-SE: 
- Esta é uma avaliação MACRO (transversal) - perguntas iguais para TODOS os profissionais
- Foco em competências UNIVERSAIS, não específicas de área
- Avalie: compreensão conceitual, raciocínio lógico, capacidade de pesquisa
- NÃO é prova com "certas" e "erradas" - cada pessoa escolhe a opção que reflete sua realidade
- **NUNCA inclua pontos ou classificações de nível nas alternativas**"""

        try:
            # Skip if LLM provider is stub
            if self.llm.provider == 'stub' or not self.llm.client:
                logger.warning("[ADAPTIVE] OpenAI not available, skipping generation")
                return None
            
            logger.info(f"[ADAPTIVE] Calling OpenAI for MACRO (transversal) question generation - block: {block_name}")
            
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um gerador de questões MACRO (transversais) para avaliação de competências universais em IA. Crie perguntas genéricas aplicáveis a TODOS os profissionais, focando em: compreensão conceitual, raciocínio lógico e capacidade de pesquisa. NÃO personalize por área ou cargo."
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
            
            # Get original choices (ordered by maturity: 1, 2, 3, 4 points)
            original_choices = question_data.get('choices', [])
            
            # Shuffle choices to prevent "D is always best" gaming
            # Create list of (choice_text, original_points)
            choices_with_points = [
                (original_choices[0], 1),  # Originally position 0 = 1 point
                (original_choices[1], 2),  # Originally position 1 = 2 points
                (original_choices[2], 3),  # Originally position 2 = 3 points
                (original_choices[3], 4),  # Originally position 3 = 4 points
            ] if len(original_choices) == 4 else [(c, i+1) for i, c in enumerate(original_choices)]
            
            # Shuffle the order
            random.shuffle(choices_with_points)
            
            # Extract shuffled choices and create points mapping
            shuffled_choices = [c[0] for c in choices_with_points]
            # points_mapping: maps position (0=A, 1=B, 2=C, 3=D) to points
            points_mapping = {i: c[1] for i, c in enumerate(choices_with_points)}
            
            logger.info(f"[ADAPTIVE] Shuffled choices. Points mapping: A={points_mapping.get(0)}, B={points_mapping.get(1)}, C={points_mapping.get(2)}, D={points_mapping.get(3)}")
            
            # Build complete item data for matrix format
            return {
                'stem': question_data.get('stem', 'Questão gerada'),
                'type': 'matrix',  # New type for matrix questions
                'block': block_name,  # Changed from 'competency' to 'block'
                'choices': shuffled_choices,  # Shuffled order
                'progressive_levels': False,  # NOT progressive anymore - order is random
                'tags': f'generated,matrix,{block_config.get("id", "unknown")}',
                'metadata': {
                    'generated': True,
                    'block_description': block_description,
                    'user_context': user_context,
                    'points_mapping': points_mapping  # NEW: maps position to points
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
