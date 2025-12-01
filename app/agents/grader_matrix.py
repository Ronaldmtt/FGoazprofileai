"""
Simplified grader for matrix-based assessment
Uses dynamic points mapping from item metadata (shuffled order)
"""

from typing import Dict, Any
from app.models import Item
import logging

logger = logging.getLogger(__name__)


class AgentGraderMatrix:
    """
    Grader for matrix questions with SHUFFLED alternatives.
    
    Points are determined by the points_mapping stored in item metadata,
    NOT by fixed position (A≠1, B≠2, etc.)
    
    This prevents gaming where users always select "D" thinking it's best.
    """
    
    # Letter to index mapping
    LETTER_TO_INDEX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    
    def grade_matrix_response(self, item: Item, answer: str) -> Dict[str, Any]:
        """
        Grade a matrix question response using dynamic points mapping.
        
        Args:
            item: Question item (contains points_mapping in metadata)
            answer: User's answer (A, B, C, or D)
        
        Returns:
            Dict with points (1-4) and normalized score
        """
        # Normalize answer to uppercase
        answer = answer.strip().upper()
        
        # Handle multi-character answers (like "OPTION_A")
        if answer not in self.LETTER_TO_INDEX:
            # Try to extract letter
            for letter in ['A', 'B', 'C', 'D']:
                if letter in answer:
                    answer = letter
                    break
        
        # Get answer index (A=0, B=1, C=2, D=3)
        answer_index = self.LETTER_TO_INDEX.get(answer, 0)
        
        # Get points mapping from item metadata
        metadata = item.get_metadata() if hasattr(item, 'get_metadata') else {}
        points_mapping = metadata.get('points_mapping', {})
        
        # Convert string keys to int if needed (JSON stores keys as strings)
        if points_mapping and isinstance(list(points_mapping.keys())[0], str):
            points_mapping = {int(k): v for k, v in points_mapping.items()}
        
        if points_mapping:
            # Use dynamic mapping (shuffled order)
            points = points_mapping.get(answer_index, 1)
            logger.info(f"[GRADER] Answer '{answer}' (index {answer_index}) → {points} points (from mapping)")
        else:
            # Fallback to legacy fixed mapping for old questions
            legacy_points = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
            points = legacy_points.get(answer, 1)
            logger.info(f"[GRADER] Answer '{answer}' → {points} points (legacy fixed mapping)")
        
        return {
            'points': points,
            'score': points / 4.0,  # Normalized 0-1 for compatibility
            'answer': answer
        }
