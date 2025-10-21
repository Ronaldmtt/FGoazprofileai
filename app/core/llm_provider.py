from typing import Dict, Any, List
import re

class LLMProvider:
    """
    Abstraction layer for LLM operations.
    MVP uses deterministic stub implementations.
    Future: integrate OpenAI/Azure APIs.
    """
    
    def __init__(self, provider: str = 'stub'):
        self.provider = provider
    
    def generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate text based on prompt.
        Stub: returns deterministic responses.
        """
        if self.provider == 'stub':
            return self._stub_generate(prompt, context)
        raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def score(self, answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an answer based on rubric.
        Returns: {score: 0-1, breakdown: {...}, flags: {...}}
        """
        if self.provider == 'stub':
            return self._stub_score(answer, rubric)
        raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def moderate(self, text: str) -> Dict[str, Any]:
        """
        Moderate content for safety/appropriateness.
        Returns: {safe: bool, flags: [...]}
        """
        if self.provider == 'stub':
            return self._stub_moderate(text)
        raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def _stub_generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Deterministic generation for testing."""
        if 'variation' in prompt.lower():
            return "Variação gerada do item original"
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
                'flags': {'incomplete': True}
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
        if len(answer) < 20:
            flags['too_short'] = True
        if len(answer) > 1000:
            flags['very_long'] = True
        
        return {
            'score': round(final_score, 2),
            'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            'flags': flags
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
