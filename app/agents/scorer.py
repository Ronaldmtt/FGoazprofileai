from typing import Dict, Any
from app.models import Item, Response, ProficiencySnapshot
from app.core.scoring import IRTScorer
from app import db

class AgentScorer:
    """
    Updates competency scores using IRT-lite algorithm.
    Maintains proficiency estimates and confidence intervals.
    """
    
    def __init__(self):
        self.irt = IRTScorer()
    
    def update_proficiency(
        self,
        session_id: int,
        item: Item,
        response_score: float,
        current_proficiency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update proficiency for the item's competency based on response.
        """
        competency = item.competency
        comp_data = current_proficiency.get(competency, {
            'score': 50.0,
            'ci_low': 20.0,
            'ci_high': 80.0,
            'items_count': 0
        })
        
        current_score = comp_data['score']
        current_ci_width = comp_data['ci_high'] - comp_data['ci_low']
        
        new_score, new_ci_width = self.irt.update_proficiency(
            current_score=current_score,
            current_ci=current_ci_width,
            item_difficulty=item.difficulty_b,
            item_discrimination=item.discrimination_a,
            response_score=response_score
        )
        
        current_proficiency[competency] = {
            'score': new_score,
            'ci_low': max(0, new_score - new_ci_width / 2),
            'ci_high': min(100, new_score + new_ci_width / 2),
            'items_count': comp_data['items_count'] + 1
        }
        
        return current_proficiency
    
    def get_current_proficiency(self, session_id: int) -> Dict[str, Any]:
        """
        Reconstruct current proficiency from session responses.
        """
        from app.agents.profiler import AgentProfiler
        from app.models import Session
        
        session = Session.query.get(session_id)
        profiler = AgentProfiler()
        proficiency = profiler.initialize_proficiency(
            session.initial_response if session.initial_response else ""
        )
        
        responses = Response.query.filter_by(session_id=session_id)\
            .order_by(Response.created_at).all()
        
        for response in responses:
            proficiency = self.update_proficiency(
                session_id,
                response.item,
                response.graded_score_0_1,
                proficiency
            )
        
        return proficiency
    
    def save_snapshot(self, session_id: int, proficiency: Dict[str, Any]):
        """Save proficiency snapshot to database."""
        ProficiencySnapshot.query.filter_by(session_id=session_id).delete()
        
        for competency, data in proficiency.items():
            snapshot = ProficiencySnapshot(
                session_id=session_id,
                competency=competency,
                score_0_100=data['score'],
                ci_low=data['ci_low'],
                ci_high=data['ci_high']
            )
            db.session.add(snapshot)
        
        db.session.commit()
