from typing import Dict, Any
from app.core.llm_provider import LLMProvider
from config import Config

class AgentProfiler:
    """
    Interprets initial response (P0) and initializes proficiency vector.
    """
    
    def __init__(self):
        self.llm = LLMProvider('stub')
    
    def initialize_proficiency(self, initial_response: str) -> Dict[str, Any]:
        """
        Initialize proficiency scores based on P0 response.
        Returns dict with competency -> {score, ci_low, ci_high}
        
        For MVP: starts all at 50/100 with high variance.
        Future: analyze P0 with LLM for better initialization.
        """
        proficiency = {}
        
        base_score = 50.0
        base_ci_width = 30.0
        
        if initial_response and len(initial_response) > 20:
            moderation = self.llm.moderate(initial_response)
            if not moderation['safe']:
                base_score = 40.0
        
        for competency in Config.COMPETENCIES:
            proficiency[competency] = {
                'score': base_score,
                'ci_low': max(0, base_score - base_ci_width),
                'ci_high': min(100, base_score + base_ci_width),
                'items_count': 0
            }
        
        return proficiency
