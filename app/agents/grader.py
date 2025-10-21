from typing import Dict, Any
from app.models import Item
from app.core.llm_provider import LLMProvider

class AgentGrader:
    """
    Grades user responses using rubrics and answer keys.
    Handles MCQ (deterministic) and open-ended (LLM-based).
    """
    
    def __init__(self):
        self.llm = LLMProvider('stub')
    
    def grade_response(self, item: Item, answer: str) -> Dict[str, Any]:
        """
        Grade response based on item type.
        Returns: {score: 0-1, breakdown: {...}, flags: {...}}
        """
        if not answer or len(answer.strip()) == 0:
            return {
                'score': 0.0,
                'breakdown': {},
                'flags': {'no_answer': True}
            }
        
        if item.type == 'mcq' or item.type == 'scenario':
            return self._grade_mcq(item, answer)
        elif item.type in ['open_ended', 'prompt_writing']:
            return self._grade_open_ended(item, answer)
        else:
            return {'score': 0.5, 'breakdown': {}, 'flags': {'unknown_type': True}}
    
    def _grade_mcq(self, item: Item, answer: str) -> Dict[str, Any]:
        """Grade multiple choice question."""
        answer_normalized = answer.strip().upper()
        
        if len(answer_normalized) > 1:
            if answer_normalized.startswith('A'):
                answer_normalized = 'A'
            elif answer_normalized.startswith('B'):
                answer_normalized = 'B'
            elif answer_normalized.startswith('C'):
                answer_normalized = 'C'
            elif answer_normalized.startswith('D'):
                answer_normalized = 'D'
        
        correct = answer_normalized == item.answer_key.upper()
        score = 1.0 if correct else 0.0
        
        return {
            'score': score,
            'breakdown': {'correct': correct},
            'flags': {}
        }
    
    def _grade_open_ended(self, item: Item, answer: str) -> Dict[str, Any]:
        """Grade open-ended or prompt writing response using LLM."""
        rubric = item.rubric or {}
        
        grading_result = self.llm.score(answer, rubric)
        
        return grading_result
