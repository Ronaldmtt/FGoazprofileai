"""
Matrix-based Orchestrator for simplified 4-block assessment
No IRT, simple additive scoring (10-40 points)
"""

from typing import Dict, Any, Optional
from app.agents.selector_matrix import AgentSelectorMatrix
from app.agents.grader_matrix import AgentGraderMatrix
from app.models import Session, Response, Item, ProficiencySnapshot
from app.core.blocks_config import BLOCKS, MATURITY_LEVELS, TOTAL_QUESTIONS
from app.services.logger import agent_logger
from app import db


class AgentOrchestratorMatrix:
    """
    Simplified orchestrator for matrix-based assessment.
    
    Flow:
    1. Present 10 questions (distributed across 4 blocks)
    2. Grade each response (1-4 points)
    3. Sum total score (10-40 points)
    4. Classify maturity level
    """
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.session = Session.query.get(session_id)
        self.selector = AgentSelectorMatrix()
        self.grader = AgentGraderMatrix()
        
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load current session state."""
        responses = Response.query.filter_by(session_id=self.session_id).all()
        
        # Build response history
        response_history = []
        total_score = 0
        block_scores = {block_name: 0 for block_name in BLOCKS.keys()}
        
        for r in responses:
            response_dict = {
                'item_id': r.item_id,
                'block': r.item.block if r.item else None,
                'matrix_points': r.matrix_points or 0,
                'stem': r.item.stem if r.item else ''
            }
            response_history.append(response_dict)
            
            # Accumulate scores
            points = r.matrix_points or 0
            total_score += points
            
            if r.item and r.item.block:
                block_scores[r.item.block] = block_scores.get(r.item.block, 0) + points
        
        return {
            'response_history': response_history,
            'items_answered': len(responses),
            'total_score': total_score,
            'block_scores': block_scores
        }
    
    def get_next_item(self) -> Optional[Item]:
        """Get next item to present to user."""
        from app.models import Session
        
        # Get user context
        session = Session.query.get(self.session_id)
        user_context = {
            'name': session.user.name if session and session.user else 'Usuário',
            'department': session.user.department if session and session.user else 'Geral',
            'role': session.user.role if session and session.user else 'Profissional'
        }
        
        return self.selector.select_next_item(
            self.session_id,
            self.state['response_history'],
            user_context
        )
    
    def process_response(self, item_id: int, answer: str, latency_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Process user response through grading pipeline.
        
        Args:
            item_id: Question ID
            answer: User's answer (A, B, C, or D)
            latency_ms: Time taken to answer
        
        Returns:
            Dict with score, updated state, next item info
        """
        item = Item.query.get(item_id)
        
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        # Grade response (1-4 points)
        grading_result = self.grader.grade_matrix_response(item, answer)
        
        # Save response
        response = Response()
        response.session_id = self.session_id
        response.item_id = item_id
        response.raw_answer = answer
        response.matrix_points = grading_result['points']
        response.graded_score_0_1 = grading_result['points'] / 4.0
        response.latency_ms = latency_ms
        
        db.session.add(response)
        db.session.commit()
        
        # Update state
        self.state['items_answered'] += 1
        self.state['total_score'] += grading_result['points']
        
        if item.block:
            self.state['block_scores'][item.block] = \
                self.state['block_scores'].get(item.block, 0) + grading_result['points']
        
        self.state['response_history'].append({
            'item_id': item_id,
            'block': item.block,
            'matrix_points': grading_result['points'],
            'stem': item.stem
        })
        
        agent_logger.event_info('orchestrator_response_processed', {
            'session_id': self.session_id,
            'item_id': item_id,
            'points': grading_result['points'],
            'total_score': self.state['total_score'],
            'items_answered': self.state['items_answered']
        })
        
        return {
            'points': grading_result['points'],
            'total_score': self.state['total_score'],
            'items_answered': self.state['items_answered'],
            'block_scores': self.state['block_scores']
        }
    
    def should_stop(self) -> Dict[str, Any]:
        """
        Check if assessment should stop.
        
        In matrix system: stops after exactly 10 questions
        """
        items_answered = self.state['items_answered']
        
        if items_answered >= TOTAL_QUESTIONS:
            return {
                'should_stop': True,
                'reason': 'all_questions_completed',
                'total_score': self.state['total_score']
            }
        
        return {
            'should_stop': False,
            'reason': 'questions_remaining',
            'remaining': TOTAL_QUESTIONS - items_answered
        }
    
    def finalize_assessment(self) -> Dict[str, Any]:
        """
        Calculate final results and save proficiency snapshot.
        
        Returns:
            Dict with total score, maturity level, block breakdown
        """
        total_score = self.state['total_score']
        block_scores = self.state['block_scores']
        
        # Determine maturity level
        maturity_level = self._classify_maturity_level(total_score)
        
        agent_logger.event_info('orchestrator_finalize_assessment', {
            'session_id': self.session_id,
            'total_score': total_score,
            'maturity_level': maturity_level['name']
        })
        
        # Save proficiency snapshot
        snapshot = ProficiencySnapshot()
        snapshot.session_id = self.session_id
        snapshot.raw_score = total_score
        snapshot.maturity_level = maturity_level['name']
        snapshot.block_scores = block_scores
        
        db.session.add(snapshot)
        
        # Update session status to completed (CRITICAL for result rendering)
        if self.session:
            self.session.status = 'completed'
            agent_logger.event_success('orchestrator_session_completed', {'session_id': self.session_id})
        else:
            agent_logger.event_error('orchestrator_session_not_found', details={'session_id': self.session_id})
        
        db.session.commit()
        
        agent_logger.event_success('orchestrator_snapshot_saved', {
            'session_id': self.session_id,
            'total_score': total_score,
            'maturity_level': maturity_level['name']
        })
        
        return {
            'total_score': total_score,
            'max_possible': TOTAL_QUESTIONS * 4,
            'maturity_level': maturity_level,
            'block_scores': block_scores,
            'block_details': self._get_block_details()
        }
    
    def _classify_maturity_level(self, total_score: int) -> Dict[str, Any]:
        """
        Classify user into maturity level based on total score.
        
        Levels:
        - Iniciante: 10-17 pts
        - Explorador: 18-27 pts
        - Praticante: 28-35 pts
        - Líder Digital: 36-40 pts
        """
        for level_name, config in MATURITY_LEVELS.items():
            if config['min_score'] <= total_score <= config['max_score']:
                return {
                    'name': level_name,
                    'display_name': config['display_name'],
                    'description': config['description'],
                    'min_score': config['min_score'],
                    'max_score': config['max_score']
                }
        
        # Fallback (shouldn't happen)
        return {
            'name': 'unknown',
            'display_name': 'Não Classificado',
            'description': 'Pontuação fora dos intervalos esperados',
            'min_score': 0,
            'max_score': 0
        }
    
    def _get_block_details(self) -> Dict[str, Any]:
        """
        Get detailed breakdown of performance per block.
        
        Returns:
            Dict with score/max_score per block and percentage
        """
        block_details = {}
        
        for block_name, config in BLOCKS.items():
            score = self.state['block_scores'].get(block_name, 0)
            max_score = config['question_count'] * 4
            percentage = (score / max_score * 100) if max_score > 0 else 0
            
            block_details[block_name] = {
                'display_name': block_name,  # Use block name directly
                'score': score,
                'max_score': max_score,
                'percentage': percentage,
                'questions_answered': config['question_count']
            }
        
        return block_details
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        return self.selector.get_progress_info(self.state['response_history'])
