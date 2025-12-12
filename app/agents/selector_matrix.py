"""
Matrix-based Selector for 4-block assessment
Simplified version without IRT complexity
"""

from typing import Dict, Any, List, Optional
from app.models import Item
from app.agents.generator import AgentGenerator
from app.core.blocks_config import BLOCKS
from app.services.logger import agent_logger
from app import db


class AgentSelectorMatrix:
    """
    Simplified selector for matrix-based assessment.
    Generates questions for 4 blocks in predetermined order.
    No IRT, no adaptive difficulty - just clean, progressive questions.
    """
    
    def __init__(self):
        self.generator = AgentGenerator()
    
    def select_next_item(
        self,
        session_id: int,
        response_history: List[Dict[str, Any]],
        user_context: dict = None
    ) -> Optional[Item]:
        """
        Select next question based on block progression.
        
        Strategy:
        1. Determine which block needs a question next
        2. Generate question for that block
        3. Return generated item
        
        Args:
            session_id: Current session ID
            response_history: List of previous responses
            user_context: User info (name, role, department)
        
        Returns:
            Generated Item or None if complete
        """
        # Get user context
        if not user_context:
            from app.models import Session
            session = Session.query.get(session_id)
            user_context = {
                'name': session.user.name if session and session.user else 'Usuário',
                'department': session.user.department if session and session.user else 'Geral',
                'role': session.user.role if session and session.user else 'Profissional'
            }
        
        # Determine next block to ask about
        next_block = self._get_next_block(response_history)
        
        if not next_block:
            agent_logger.event_info('selector_all_questions_completed', {'session_id': session_id})
            return None
        
        agent_logger.event_info('selector_generating_question', {'session_id': session_id, 'block': next_block})
        
        # Generate question for this block
        generated_data = self.generator.generate_matrix_question(
            block_name=next_block,
            response_history=response_history,
            user_context=user_context
        )
        
        if not generated_data:
            agent_logger.event_error('selector_generation_failed', details={'block': next_block, 'session_id': session_id})
            return None
        
        # Create and save item
        generated_item = Item(
            stem=generated_data['stem'],
            type=generated_data.get('type', 'matrix'),
            block=next_block,
            choices=generated_data.get('choices', []),
            progressive_levels=True,
            tags='generated,matrix',
            active=True
        )
        
        # Set metadata
        if 'metadata' in generated_data:
            generated_item.set_metadata(generated_data['metadata'])
        
        db.session.add(generated_item)
        db.session.commit()
        
        agent_logger.event_success('selector_item_created', {'item_id': generated_item.id, 'block': next_block, 'session_id': session_id})
        return generated_item
    
    def _get_next_block(self, response_history: List[Dict[str, Any]]) -> Optional[str]:
        """
        Determine which block should receive the next question.
        
        Distribution (10 questions total):
        - Percepção e Atitude: 3 questions
        - Uso Prático: 3 questions
        - Conhecimento e Entendimento: 2 questions
        - Cultura e Autonomia Digital: 2 questions
        
        Returns:
            Block name or None if all complete
        """
        # Count questions per block
        block_counts = {}
        for block_name, config in BLOCKS.items():
            block_counts[block_name] = 0
        
        # Count existing responses
        for response in response_history:
            block = response.get('block')
            if block and block in block_counts:
                block_counts[block] += 1
        
        agent_logger.event_info('selector_block_distribution', block_counts)
        
        # Find next block that needs questions
        for block_name, config in BLOCKS.items():
            target_count = config['question_count']
            current_count = block_counts.get(block_name, 0)
            
            if current_count < target_count:
                agent_logger.event_info('selector_next_block', {'block': block_name, 'current': current_count, 'target': target_count})
                return block_name
        
        # All blocks complete
        return None
    
    def get_progress_info(self, response_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get information about assessment progress.
        
        Returns:
            Dict with total questions, completed, remaining, per-block stats
        """
        from app.core.blocks_config import TOTAL_QUESTIONS
        
        block_counts = {}
        for block_name, config in BLOCKS.items():
            block_counts[block_name] = {
                'completed': 0,
                'target': config['question_count']
            }
        
        for response in response_history:
            block = response.get('block')
            if block and block in block_counts:
                block_counts[block]['completed'] += 1
        
        total_completed = len(response_history)
        
        return {
            'total_questions': TOTAL_QUESTIONS,
            'completed': total_completed,
            'remaining': TOTAL_QUESTIONS - total_completed,
            'progress_percentage': (total_completed / TOTAL_QUESTIONS * 100) if TOTAL_QUESTIONS > 0 else 0,
            'blocks': block_counts
        }
