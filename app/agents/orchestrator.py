from typing import Dict, Any, Optional
from app.agents.profiler import AgentProfiler
from app.agents.selector import AgentSelector
from app.agents.grader import AgentGrader
from app.agents.scorer import AgentScorer
from app.agents.recommender import AgentRecommender
from app.models import Session, Response, Item
from app import db

class AgentOrchestrator:
    """
    Central orchestrator for the assessment agent ecosystem.
    Maintains session state and coordinates between agents.
    """
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.session = Session.query.get(session_id)
        self.profiler = AgentProfiler()
        self.selector = AgentSelector()
        self.grader = AgentGrader()
        self.scorer = AgentScorer()
        self.recommender = AgentRecommender()
        
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load or initialize session state."""
        responses = Response.query.filter_by(session_id=self.session_id).all()
        
        if not responses:
            proficiency_state = self.profiler.initialize_proficiency(
                self.session.initial_response if self.session.initial_response else ""
            )
        else:
            proficiency_state = self.scorer.get_current_proficiency(self.session_id)
        
        return {
            'proficiency': proficiency_state,
            'items_answered': len(responses),
            'response_history': [
                {
                    'item_id': r.item_id,
                    'competency': r.item.competency,
                    'type': r.item.type,
                    'score': r.graded_score_0_1
                }
                for r in responses
            ]
        }
    
    def get_next_item(self) -> Optional[Item]:
        """Get next item to present to user."""
        return self.selector.select_next_item(
            self.session_id,
            self.state['proficiency'],
            self.state['response_history']
        )
    
    def process_response(self, item_id: int, answer: str, latency_ms: int = None) -> Dict[str, Any]:
        """
        Process user response through grading and scoring pipeline.
        Returns updated state and next item info.
        """
        item = Item.query.get(item_id)
        
        grading_result = self.grader.grade_response(item, answer)
        
        response = Response(
            session_id=self.session_id,
            item_id=item_id,
            raw_answer=answer,
            graded_score_0_1=grading_result['score'],
            latency_ms=latency_ms
        )
        response.rubric_breakdown = grading_result.get('breakdown', {})
        response.ai_flags = grading_result.get('flags', {})
        db.session.add(response)
        db.session.commit()
        
        self.state['proficiency'] = self.scorer.update_proficiency(
            self.session_id,
            item,
            grading_result['score'],
            self.state['proficiency']
        )
        
        self.state['items_answered'] += 1
        self.state['response_history'].append({
            'item_id': item_id,
            'competency': item.competency,
            'type': item.type,
            'score': grading_result['score']
        })
        
        return {
            'score': grading_result['score'],
            'proficiency_update': self.state['proficiency'],
            'items_answered': self.state['items_answered']
        }
    
    def should_stop(self) -> Dict[str, Any]:
        """Check if session should stop based on criteria."""
        from datetime import datetime
        from config import Config
        
        items_answered = self.state['items_answered']
        
        if items_answered >= Config.MAX_ITEMS_PER_SESSION:
            return {'should_stop': True, 'reason': 'max_items'}
        
        if items_answered < Config.MIN_ITEMS_PER_SESSION:
            return {'should_stop': False, 'reason': 'min_not_reached'}
        
        time_spent = (datetime.utcnow() - self.session.started_at).total_seconds() / 60
        if time_spent >= Config.TARGET_SESSION_TIME_MINUTES:
            return {'should_stop': True, 'reason': 'time_limit'}
        
        converged_count = sum(
            1 for comp_data in self.state['proficiency'].values()
            if (comp_data['ci_high'] - comp_data['ci_low']) <= Config.CONVERGENCE_CI_THRESHOLD
        )
        
        if converged_count >= Config.CONVERGENCE_MIN_COMPETENCIES:
            return {'should_stop': True, 'reason': 'convergence'}
        
        return {'should_stop': False, 'reason': 'continue'}
    
    def generate_recommendations(self) -> Dict[str, Any]:
        """Generate learning recommendations based on final proficiency."""
        return self.recommender.generate_recommendations(
            self.state['proficiency']
        )
