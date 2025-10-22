from typing import Dict, Any, List
import re
import os
import json
import logging

# Reference: using blueprint:python_openai integration
# Using gpt-4o model (latest production model)
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMProvider:
    """
    Abstraction layer for LLM operations.
    Supports OpenAI (production) and stub (testing).
    """
    
    def __init__(self, provider: str = 'openai'):
        self.provider = provider
        self.client = None
        
        if self.provider == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not found, falling back to stub")
                self.provider = 'stub'
            else:
                self.client = OpenAI(api_key=api_key)
    
    def generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate text based on prompt.
        Used for question variations and recommendations.
        """
        if self.provider == 'openai':
            return self._openai_generate(prompt, context)
        return self._stub_generate(prompt, context)
    
    def score(self, answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an answer based on rubric using intelligent analysis.
        Returns: {score: 0-1, breakdown: {...}, flags: {...}, feedback: str}
        """
        if self.provider == 'openai':
            return self._openai_score(answer, rubric)
        return self._stub_score(answer, rubric)
    
    def moderate(self, text: str) -> Dict[str, Any]:
        """
        Moderate content for safety/appropriateness.
        Returns: {safe: bool, flags: [...]}
        """
        if self.provider == 'openai':
            return self._openai_moderate(text)
        return self._stub_moderate(text)
    
    # ===== OpenAI Real Implementations =====
    
    def _openai_generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate text using GPT-5."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em inteligência artificial e tecnologia. Seja conciso, técnico e preciso."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            if context:
                messages[0]["content"] += f"\n\nContexto: {json.dumps(context, ensure_ascii=False)}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_completion_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI generate error: {e}")
            return self._stub_generate(prompt, context)
    
    def _openai_score(self, answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score answer using GPT-5 with rubric-based evaluation.
        Provides detailed breakdown and constructive feedback.
        """
        try:
            rubric_str = "\n".join([f"- {k}: {v}" for k, v in rubric.items()])
            
            system_prompt = """Você é um avaliador especialista em proficiência de IA.
Avalie a resposta do usuário com base na rubrica fornecida.

Retorne um JSON com:
- score: pontuação geral de 0 a 1
- breakdown: objeto com pontuação (0-1) para cada critério da rubrica
- feedback: texto breve (2-3 frases) com pontos fortes e áreas de melhoria
- flags: objeto com flags opcionais (too_short, incomplete, excellent, etc)

Seja justo mas exigente. Respostas superficiais recebem < 0.5, médias ~0.6-0.7, excelentes > 0.8."""
            
            user_prompt = f"""Rubrica de avaliação:
{rubric_str}

Resposta do usuário:
"{answer}"

Avalie e retorne o JSON."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=400
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and normalize
            if 'score' not in result:
                result['score'] = 0.5
            if 'breakdown' not in result:
                result['breakdown'] = {}
            if 'feedback' not in result:
                result['feedback'] = "Avaliação concluída."
            if 'flags' not in result:
                result['flags'] = {}
            
            # Ensure score is between 0 and 1
            result['score'] = max(0.0, min(1.0, float(result['score'])))
            
            logger.info(f"OpenAI scoring: {result['score']:.2f} for answer length {len(answer)}")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI score error: {e}")
            return self._stub_score(answer, rubric)
    
    def _openai_moderate(self, text: str) -> Dict[str, Any]:
        """Moderate content using OpenAI moderation API."""
        try:
            # OpenAI moderation endpoint
            response = self.client.moderations.create(input=text)
            result = response.results[0]
            
            flags = []
            if result.flagged:
                for category, flagged in result.categories.model_dump().items():
                    if flagged:
                        flags.append(category)
            
            return {
                'safe': not result.flagged,
                'flags': flags
            }
            
        except Exception as e:
            logger.error(f"OpenAI moderate error: {e}")
            return self._stub_moderate(text)
    
    # ===== Stub Implementations (for testing) =====
    
    def _stub_generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Deterministic generation for testing."""
        if 'variation' in prompt.lower():
            return "Variação gerada do item original"
        if 'recomenda' in prompt.lower():
            return "Recomendação: Estude fundamentos de IA e pratique com ferramentas reais."
        return "Resposta gerada pelo LLM stub"
    
    def _stub_score(self, answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic scoring based on answer characteristics.
        """
        if not answer or len(answer.strip()) < 5:
            return {
                'score': 0.0,
                'breakdown': {
                    'relevancia': 0.0,
                    'precisao': 0.0,
                    'seguranca': 0.5,
                    'completude': 0.0,
                    'objetividade': 0.0
                },
                'flags': {'incomplete': True},
                'feedback': 'Resposta muito curta ou incompleta.'
            }
        
        answer_lower = answer.lower()
        
        keywords_good = ['ia', 'inteligência artificial', 'llm', 'prompt', 'automação', 
                        'dados', 'modelo', 'contexto', 'ética', 'segurança']
        keywords_count = sum(1 for kw in keywords_good if kw in answer_lower)
        
        length_score = min(len(answer) / 200, 1.0)
        keyword_score = min(keywords_count / 3, 1.0)
        
        base_score = (length_score * 0.4 + keyword_score * 0.6)
        
        breakdown = {
            'relevancia': min(keyword_score + 0.2, 1.0),
            'precisao': min(base_score + 0.1, 1.0),
            'seguranca': 0.8,
            'completude': min(length_score + 0.1, 1.0),
            'objetividade': min(base_score, 1.0)
        }
        
        final_score = sum(breakdown.values()) / len(breakdown)
        
        flags = {}
        feedback_parts = []
        
        if len(answer) < 20:
            flags['too_short'] = True
            feedback_parts.append("Resposta muito curta.")
        if len(answer) > 1000:
            flags['very_long'] = True
            feedback_parts.append("Resposta muito extensa.")
        if keywords_count >= 3:
            flags['good_keywords'] = True
            feedback_parts.append("Boa utilização de termos técnicos.")
        
        if not feedback_parts:
            feedback_parts.append("Resposta adequada.")
        
        return {
            'score': round(final_score, 2),
            'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            'flags': flags,
            'feedback': ' '.join(feedback_parts)
        }
    
    def _stub_moderate(self, text: str) -> Dict[str, Any]:
        """Simple content moderation."""
        unsafe_patterns = ['<script', 'javascript:', 'onerror=']
        flags = []
        
        text_lower = text.lower()
        for pattern in unsafe_patterns:
            if pattern in text_lower:
                flags.append(f'unsafe_content: {pattern}')
        
        return {
            'safe': len(flags) == 0,
            'flags': flags
        }
