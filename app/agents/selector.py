from typing import Dict, Any, List, Optional
from app.models import Item, Response
from app.agents.generator import AgentGenerator
from app import db
import random
import logging

logger = logging.getLogger(__name__)

class AgentSelector:
    """
    Selects next question to maximize information gain.
    Can use existing items OR generate adaptive questions dynamically.
    """
    
    def __init__(self):
        self.generator = AgentGenerator()
    
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
        - Dynamic generation when appropriate
        - No repetition
        """
        # Get user info for personalization
        from app.models import Session
        session = Session.query.get(session_id)
        user_context = {
            'name': session.user.name if session and session.user else 'Usuário',
            'department': session.user.department if session and session.user else 'Geral',
            'role': session.user.role if session and session.user else 'Profissional'
        }
        
        answered_ids = [r['item_id'] for r in response_history]
        
        available_items = Item.query.filter(
            Item.active == True,
            ~Item.id.in_(answered_ids) if answered_ids else True
        ).all()
        
        if not available_items:
            return None
        
        last_competency = response_history[-1]['competency'] if response_history else None
        last_type = response_history[-1]['type'] if response_history else None
        
        # Score existing items
        scored_items = []
        for item in available_items:
            score = self._score_item(item, proficiency, last_competency, last_type)
            scored_items.append((score, item))
        
        scored_items.sort(reverse=True, key=lambda x: x[0])
        
        # Decide: use existing question or generate adaptive one?
        should_generate = self._should_generate_adaptive(proficiency, response_history)
        
        logger.info(f"[ADAPTIVE] should_generate={should_generate}, history_length={len(response_history)}")
        
        if should_generate:
            # Generate adaptive question for competency needing focus
            target_comp = self._select_target_competency(proficiency, response_history)
            difficulty = self._determine_difficulty(proficiency.get(target_comp, {}))
            
            logger.info(f"[ADAPTIVE] Generating question for {target_comp} at {difficulty} level")
            
            generated_data = self.generator.generate_adaptive_question(
                competency=target_comp,
                current_score=proficiency.get(target_comp, {}).get('score', 50),
                difficulty_target=difficulty,
                response_history=response_history,
                user_context=user_context
            )
            
            if generated_data:
                logger.info(f"[ADAPTIVE] Successfully generated question: {generated_data['stem'][:80]}...")
                # Create and save generated item
                generated_item = Item(
                    stem=generated_data['stem'],
                    type=generated_data['type'],
                    competency=generated_data['competency'],
                    difficulty_b=generated_data['difficulty_b'],
                    discrimination_a=generated_data['discrimination_a'],
                    choices=generated_data.get('choices'),
                    answer_key=generated_data.get('answer_key'),
                    rubric=generated_data.get('rubric'),
                    tags=generated_data.get('tags', ''),
                    active=True
                )
                db.session.add(generated_item)
                db.session.commit()
                
                logger.info(f"[ADAPTIVE] Created item ID {generated_item.id} in database")
                return generated_item
            else:
                # NO FALLBACK - if generation fails, return None to indicate error
                logger.error("[ADAPTIVE] Generation FAILED - OpenAI did not generate question")
                return None
    
    def _should_generate_adaptive(
        self,
        proficiency: Dict[str, Any],
        response_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Decide if we should generate adaptive question vs. use existing.
        NOW: Always generate adaptive questions (100% personalized)
        """
        # ALWAYS generate personalized questions using OpenAI
        return True
    
    def _select_target_competency(
        self,
        proficiency: Dict[str, Any],
        response_history: List[Dict[str, Any]]
    ) -> str:
        """
        Select which competency should receive the next adaptive question.
        Prioritize:
        1. Competencies with high uncertainty (wide CI)
        2. Competencies not recently tested
        3. Competencies with low item count
        """
        recent_competencies = [r['competency'] for r in response_history[-3:]]
        
        # Score competencies by priority
        comp_scores = []
        for comp, data in proficiency.items():
            score = 0.0
            
            # Prioritize high uncertainty
            ci_width = data.get('ci_high', 80) - data.get('ci_low', 20)
            if ci_width > 25:
                score += 10.0
            elif ci_width > 15:
                score += 5.0
            
            # Avoid recently tested
            if comp not in recent_competencies:
                score += 8.0
            
            # Prioritize low coverage
            items_count = data.get('items_count', 0)
            if items_count < 2:
                score += 12.0
            elif items_count < 4:
                score += 6.0
            
            comp_scores.append((score, comp))
        
        if comp_scores:
            comp_scores.sort(reverse=True)
            # Pick from top 3
            top_comps = [c for _, c in comp_scores[:3]]
            return random.choice(top_comps)
        
        # Fallback
        return list(proficiency.keys())[0] if proficiency else "Fundamentos de IA/ML & LLMs"
    
    def _determine_difficulty(self, comp_data: Dict[str, Any]) -> str:
        """
        Determine difficulty level for generated question based on user's score.
        """
        score = comp_data.get('score', 50)
        
        if score < 35:
            return 'easy'
        elif score < 65:
            return 'medium'
        else:
            return 'hard'
    
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
        
        # Match difficulty to user level
        difficulty_map = {0: 30, 1: 50, 2: 70}
        item_difficulty_score = difficulty_map.get(int(item.difficulty_b), 50)
        
        score_diff = abs(comp_score - item_difficulty_score)
        if score_diff < 20:
            score += 10.0
        elif score_diff < 35:
            score += 5.0
        
        # Prioritize high uncertainty
        if ci_width > 25:
            score += 8.0
        elif ci_width > 15:
            score += 4.0
        
        # Item quality
        score += item.discrimination_a * 10
        
        # Diversity
        if item.competency != last_competency:
            score += 5.0
        
        if item.type != last_type:
            score += 3.0
        
        # Coverage
        items_in_competency = comp_data.get('items_count', 0)
        if items_in_competency == 0:
            score += 12.0
        elif items_in_competency == 1:
            score += 6.0
        
        return score
