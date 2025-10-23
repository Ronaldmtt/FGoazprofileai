"""
Simplified grader for matrix-based assessment
Maps answer choices (A/B/C/D) to points (1/2/3/4)
"""

from typing import Dict, Any
from app.models import Item
import logging

logger = logging.getLogger(__name__)


class AgentGraderMatrix:
    """
    Simplified grader for matrix questions.
    
    Scoring:
    - Option A = 1 point (lowest maturity)
    - Option B = 2 points
    - Option C = 3 points
    - Option D = 4 points (highest maturity)
    """
    
    def grade_matrix_response(self, item: Item, answer: str) -> Dict[str, Any]:
        """
        Grade a matrix question response.
        
        Args:
            item: Question item
            answer: User's answer (A, B, C, or D)
        
        Returns:
            Dict with points (1-4) and normalized score
        """
        # Normalize answer to uppercase
        answer = answer.strip().upper()
        
        # Map answer to points
        answer_to_points = {
            'A': 1,
            'B': 2,
            'C': 3,
            'D': 4
        }
        
        # Handle multi-character answers (like "OPTION_A")
        if answer not in answer_to_points:
            # Try to extract letter
            for letter in ['A', 'B', 'C', 'D']:
                if letter in answer:
                    answer = letter
                    break
        
        points = answer_to_points.get(answer, 1)  # Default to 1 if invalid
        
        logger.info(f"[GRADER] Answer '{answer}' → {points} points")
        
        return {
            'points': points,
            'score': points / 4.0,  # Normalized 0-1 for compatibility
            'answer': answer
        }
