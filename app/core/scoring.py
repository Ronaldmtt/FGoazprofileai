import math
from typing import Dict, Tuple

class IRTScorer:
    
    @staticmethod
    def _score_to_theta(score_0_100: float) -> float:
        """
        Convert 0-100 score to theta (ability parameter on z-scale).
        Maps: 0 → -3, 50 → 0, 100 → +3
        """
        return (score_0_100 - 50) / 16.67  # ±3 sigma
    
    @staticmethod
    def _theta_to_score(theta: float) -> float:
        """
        Convert theta back to 0-100 score.
        Maps: -3 → 0, 0 → 50, +3 → 100
        """
        score = 50 + (theta * 16.67)
        return max(0, min(100, score))
    
    @staticmethod
    def update_proficiency(
        current_score: float,
        current_ci: float,
        item_difficulty: float,
        item_discrimination: float,
        response_score: float
    ) -> Tuple[float, float]:
        """
        IRT-based update using proper logistic model with theta scale.
        
        Args:
            current_score: Current proficiency (0-100)
            current_ci: Current confidence interval width  
            item_difficulty: Item difficulty b parameter (-3 to +3 theta scale)
            item_discrimination: Item discrimination a parameter (0.5-2.5)
            response_score: Response score (0-1, 0=incorrect, 1=correct)
        
        Returns:
            (new_score, new_ci)
        """
        # Convert current score to theta scale
        theta = IRTScorer._score_to_theta(current_score)
        
        # IRT logistic model: P(correct) = 1 / (1 + exp(-a*(theta - b)))
        # Calculate expected probability of correct response
        z = item_discrimination * (theta - item_difficulty)
        expected_prob = 1 / (1 + math.exp(-z))
        
        # Bayesian update: move theta toward where performance suggests
        # If scored better than expected → increase theta
        # If scored worse than expected → decrease theta
        performance_gap = response_score - expected_prob
        
        # Learning rate scales with discrimination (more informative items = bigger updates)
        learning_rate = 0.3 * item_discrimination
        theta_update = learning_rate * performance_gap
        
        new_theta = theta + theta_update
        
        # Clamp theta to reasonable range (-3 to +3)
        new_theta = max(-3, min(3, new_theta))
        
        # Convert back to 0-100 scale
        new_score = IRTScorer._theta_to_score(new_theta)
        
        # Reduce CI with each response (increasing confidence)
        new_ci = current_ci * 0.85
        
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
