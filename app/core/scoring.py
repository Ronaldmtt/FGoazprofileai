import math
from typing import Dict, Tuple

class IRTScorer:
    
    @staticmethod
    def update_proficiency(
        current_score: float,
        current_ci: float,
        item_difficulty: float,
        item_discrimination: float,
        response_score: float
    ) -> Tuple[float, float]:
        """
        IRT-lite update: adjust proficiency based on item response.
        
        Args:
            current_score: Current proficiency (0-100)
            current_ci: Current confidence interval width
            item_difficulty: Item difficulty (0=easy, 1=medium, 2=hard)
            item_discrimination: Item discrimination (0-1, higher = more informative)
            response_score: Response score (0-1, 0=incorrect, 1=correct)
        
        Returns:
            (new_score, new_ci)
        """
        difficulty_map = {0: 30, 1: 50, 2: 70}
        difficulty_threshold = difficulty_map.get(int(item_difficulty), 50)
        
        max_change = 15 * item_discrimination
        
        if response_score >= 0.8:
            if difficulty_threshold > current_score:
                delta = max_change * (difficulty_threshold - current_score) / 50
            else:
                delta = max_change * 0.5
        elif response_score <= 0.2:
            if difficulty_threshold < current_score:
                delta = -max_change * (current_score - difficulty_threshold) / 50
            else:
                delta = -max_change * 0.5
        else:
            delta = (response_score - 0.5) * max_change * 0.5
        
        new_score = max(0, min(100, current_score + delta))
        
        new_ci = current_ci * 0.8
        
        return new_score, new_ci
    
    @staticmethod
    def calculate_level(score: float) -> str:
        """Calculate proficiency level (N0-N5) based on score."""
        if score < 30:
            return 'N0'
        elif score < 45:
            return 'N1'
        elif score < 60:
            return 'N2'
        elif score < 75:
            return 'N3'
        elif score < 90:
            return 'N4'
        else:
            return 'N5'
    
    @staticmethod
    def calculate_global_score(competency_scores: Dict[str, float]) -> float:
        """Calculate weighted global score from competency scores."""
        if not competency_scores:
            return 50.0
        return sum(competency_scores.values()) / len(competency_scores)
