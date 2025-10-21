from typing import Dict, Any, List, Optional
from app.models import Item, Response
from app import db
import random

class AgentSelector:
    """
    Selects next question to maximize information gain.
    Uses IRT-lite heuristics and diversification rules.
    """
    
    def select_next_item(
        self,
        session_id: int,
        proficiency: Dict[str, Any],
        response_history: List[Dict[str, Any]]
    ) -> Optional[Item]:
        """
        Select optimal next item based on:
        - Current proficiency estimates
        - Competency coverage diversity
        - Item type variation
        - No repetition
        """
        answered_ids = [r['item_id'] for r in response_history]
        
        available_items = Item.query.filter(
            Item.active == True,
            ~Item.id.in_(answered_ids) if answered_ids else True
        ).all()
        
        if not available_items:
            return None
        
        last_competency = response_history[-1]['competency'] if response_history else None
        last_type = response_history[-1]['type'] if response_history else None
        
        scored_items = []
        for item in available_items:
            score = self._score_item(item, proficiency, last_competency, last_type)
            scored_items.append((score, item))
        
        scored_items.sort(reverse=True, key=lambda x: x[0])
        
        top_k = min(5, len(scored_items))
        selected = random.choice(scored_items[:top_k])[1]
        
        return selected
    
    def _score_item(
        self,
        item: Item,
        proficiency: Dict[str, Any],
        last_competency: Optional[str],
        last_type: Optional[str]
    ) -> float:
        """
        Score item for selection based on multiple factors.
        Higher score = better candidate.
        """
        score = 0.0
        
        comp_data = proficiency.get(item.competency, {})
        comp_score = comp_data.get('score', 50)
        ci_width = comp_data.get('ci_high', 80) - comp_data.get('ci_low', 20)
        
        difficulty_map = {0: 30, 1: 50, 2: 70}
        item_difficulty_score = difficulty_map.get(int(item.difficulty_b), 50)
        
        score_diff = abs(comp_score - item_difficulty_score)
        if score_diff < 20:
            score += 10.0
        elif score_diff < 35:
            score += 5.0
        
        if ci_width > 25:
            score += 8.0
        elif ci_width > 15:
            score += 4.0
        
        score += item.discrimination_a * 10
        
        if item.competency != last_competency:
            score += 5.0
        
        if item.type != last_type:
            score += 3.0
        
        items_in_competency = comp_data.get('items_count', 0)
        if items_in_competency == 0:
            score += 12.0
        elif items_in_competency == 1:
            score += 6.0
        
        return score
