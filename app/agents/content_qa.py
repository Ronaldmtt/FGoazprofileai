from typing import Dict, Any, List
from app.core.llm_provider import LLMProvider
from config import Config

class AgentContentQA:
    """
    Validates new assessment items for quality and appropriateness.
    """
    
    def __init__(self):
        self.llm = LLMProvider('stub')
    
    def validate_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate item quality across multiple dimensions.
        Returns: {valid: bool, issues: [...], score: 0-1}
        """
        issues = []
        score = 1.0
        
        if not item_data.get('stem') or len(item_data['stem']) < 10:
            issues.append('Enunciado muito curto ou ausente')
            score -= 0.3
        
        if item_data.get('stem') and len(item_data['stem']) > 1000:
            issues.append('Enunciado muito longo')
            score -= 0.1
        
        if item_data.get('competency') not in Config.COMPETENCIES:
            issues.append(f"Competência inválida: {item_data.get('competency')}")
            score -= 0.4
        
        item_type = item_data.get('type')
        valid_types = ['mcq', 'scenario', 'open_ended', 'prompt_writing']
        if item_type not in valid_types:
            issues.append(f'Tipo inválido: {item_type}. Deve ser um de {valid_types}')
            score -= 0.3
        
        if item_type in ['mcq', 'scenario']:
            choices = item_data.get('choices', [])
            if not choices or len(choices) < 2:
                issues.append('MCQ deve ter pelo menos 2 alternativas')
                score -= 0.4
            
            if not item_data.get('answer_key'):
                issues.append('MCQ deve ter gabarito (answer_key)')
                score -= 0.4
        
        if item_type in ['open_ended', 'prompt_writing']:
            if not item_data.get('rubric'):
                issues.append('Questões abertas devem ter rubrica de correção')
                score -= 0.3
        
        difficulty = item_data.get('difficulty_b', 1.0)
        if difficulty < 0 or difficulty > 2:
            issues.append('Dificuldade deve estar entre 0 e 2')
            score -= 0.1
        
        discrimination = item_data.get('discrimination_a', 0.5)
        if discrimination < 0 or discrimination > 1:
            issues.append('Discriminação deve estar entre 0 e 1')
            score -= 0.1
        
        moderation = self.llm.moderate(item_data.get('stem', ''))
        if not moderation['safe']:
            issues.append(f"Conteúdo inapropriado detectado: {moderation['flags']}")
            score -= 0.5
        
        return {
            'valid': len(issues) == 0,
            'score': max(0, score),
            'issues': issues
        }
