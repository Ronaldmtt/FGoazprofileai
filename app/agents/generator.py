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
        # Higher discrimination (a) for better separation between correct/incorrect
        difficulty_map = {
            'easy': {'b': -1.0, 'a': 1.5, 'description': 'básico/introdutório'},
            'medium': {'b': 0.0, 'a': 1.8, 'description': 'intermediário/prático'},
            'hard': {'b': 1.5, 'a': 2.2, 'description': 'avançado/especialista'}
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
        format_type = random.choice(['practical', 'tool_usage', 'real_scenario', 'decision', 'application'])
        
        # Simplify based on difficulty
        level_guidance = {
            'easy': 'Perguntas SIMPLES para quem está começando a usar IA no trabalho',
            'medium': 'Perguntas práticas para quem já usa IA regularmente',
            'hard': 'Perguntas para especialistas que dominam IA profundamente'
        }
        
        prompt = f"""Você é um especialista em criar avaliações DESAFIADORAS de uso de IA no trabalho.

CONTEXTO DA AVALIAÇÃO:
- **Objetivo**: Identificar com PRECISÃO o nível de conhecimento em IA dos colaboradores da OAZ
- **Público**: Todos os funcionários (desde quem nunca usou IA até especialistas)
- **Finalidade**: Direcionar pessoas para treinamentos adequados ao seu nível
- **CRÍTICO**: As alternativas devem ser SUTIS e AMBÍGUAS, não óbvias

DADOS DO USUÁRIO:
- Competência avaliada: {competency}
- Cargo: {user_context['role']}
- Área: {user_context['department']}
- Nível atual: {diff_params['description']}

{level_guidance[difficulty_target]}

INSTRUÇÕES PARA CRIAR A PERGUNTA:

1. **SEJA DIRETO E PRÁTICO**: 
   - Pergunte sobre situações REAIS de trabalho
   - Use linguagem simples e clara
   - Foque em "como fazer" ou "o que usar"

2. **EXEMPLOS DE PERGUNTAS BOAS**:
   - "Você precisa resumir 50 páginas de um relatório. Qual abordagem é mais eficiente?"
   - "Sua equipe quer automatizar respostas a emails comuns. O que considerar primeiro?"
   - "Você precisa criar uma apresentação sobre vendas. Qual estratégia funciona melhor?"
   - "Um cliente pergunta sobre privacidade ao usar ChatGPT. Qual afirmação está correta?"

3. **DIFICULDADE POR NÍVEL**:
   - **Básico**: Situações simples de uso de IA, mas com opções que se sobrepõem
   - **Intermediário**: Cenários que exigem escolha entre opções TODAS plausíveis
   - **Avançado**: Casos com nuances técnicas, limitações e trade-offs sutis

4. **ALTERNATIVAS - REGRAS CRÍTICAS DE AMBIGUIDADE**:

   ⚠️ **ATENÇÃO MÁXIMA**: Este é o ponto mais importante!

   **TODAS as 4 alternativas DEVEM**:
   ✓ Parecer plausíveis à primeira vista
   ✓ Conter elementos parcialmente corretos (exceto a incorreta óbvia)
   ✓ Usar linguagem similar entre si (mesmo nível de formalidade)
   ✓ Ter comprimento similar (evite uma muito longa e outras curtas)

   **Técnicas para criar AMBIGUIDADE**:
   
   a) **Misture verdades parciais**:
      - Opção correta: "Use ChatGPT com contexto específico e valide as informações"
      - Distrator bom: "Use ChatGPT diretamente, pois sempre fornece dados corretos" (parcialmente correto, mas falha na validação)
      - Distrator ruim: "Nunca use IA para isso" (muito óbvio)

   b) **Crie trade-offs sutis**:
      - Todas opções funcionam, mas UMA é MELHOR para o contexto específico
      - Exemplo: diferentes ferramentas que resolvem, mas uma é mais adequada

   c) **Simule erros comuns de humanos**:
      - Inclua misconceptions frequentes
      - Exemplo: "IA sempre precisa de internet" vs "IA pode funcionar offline em alguns casos"

   d) **Use qualificadores sutis**:
      - "sempre", "nunca", "na maioria dos casos", "geralmente"
      - A diferença entre correto/incorreto está NO QUALIFICADOR

   e) **Sobreponha conceitos**:
      - Opções que misturam ferramentas/conceitos relacionados
      - Exemplo: ChatGPT vs Copilot vs Gemini - todos são LLMs, mas têm usos diferentes

   **EXEMPLO DE ALTERNATIVAS BEM CONSTRUÍDAS**:
   
   Pergunta: "Você precisa analisar sentimento de 1000 reviews de clientes. Qual abordagem é mais eficiente?"
   
   A) Usar ChatGPT copiando reviews em lotes de 50, pedindo análise estruturada ✓ CORRETA
   B) Usar ChatGPT copiando todos os 1000 reviews de uma vez para análise completa (parece certo, mas excede limite de contexto)
   C) Ler manualmente para entender nuances, depois usar IA para confirmar (muito lento, mas não está errado)
   D) Usar Google Sheets com fórmulas de análise de texto nativas (tecnicamente possível, mas limitado)

   ❌ **EVITE CRIAR**:
   - Opções obviamente absurdas: "Use uma máquina de escrever"
   - Opções muito técnicas: "Implemente um transformer BERT com fine-tuning"
   - Opções que ninguém consideraria: "Contrate 100 pessoas"

5. **DISTRIBUIÇÃO DAS ALTERNATIVAS**:
   - 1 claramente correta (mas não óbvia)
   - 2 parcialmente corretas com falhas sutis
   - 1 plausível mas inadequada ao contexto

6. **NÃO FAÇA**:
   ❌ Alternativas com comprimentos muito diferentes
   ❌ Uma opção muito técnica e outras muito simples
   ❌ Opções que se contradizem completamente (fica óbvio)
   ❌ Usar sempre a mesma posição para resposta correta (varie A/B/C/D)

RETORNE JSON:
{{
  "stem": "Pergunta DIRETA sobre uso prático de IA no trabalho",
  "choices": [
    "A) Primeira opção (sutil, plausível, parcialmente correta)",
    "B) Segunda opção (sutil, plausível, parcialmente correta)", 
    "C) Terceira opção (CORRETA mas não óbvia)",
    "D) Quarta opção (plausível mas com limitação clara ao analisar)"
  ],
  "answer_key": "A/B/C/D (varie a posição!)",
  "explanation": "Explicação que mostre POR QUE as outras opções, apesar de plausíveis, não são ideais",
  "rubric_criteria": {{"uso_pratico": "sabe usar IA no trabalho", "conhecimento": "entende quando aplicar"}},
  "distractor_quality": "Explicação de por que os distratores são sutis e desafiadores"
}}

LEMBRE-SE: Se for fácil identificar a resposta correta em 2 segundos, a questão FALHOU! O usuário deve PENSAR e COMPARAR as opções!"""

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
