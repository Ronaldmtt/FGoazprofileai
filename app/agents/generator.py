from typing import Dict, Any
from app.core.llm_provider import LLMProvider

class AgentGenerator:
    """
    Generates question variations and validates language clarity.
    Future: create new items dynamically.
    """
    
    def __init__(self):
        self.llm = LLMProvider('stub')
    
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
