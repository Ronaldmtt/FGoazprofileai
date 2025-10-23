from typing import Dict, Any, List, Optional
from app.models import Item, Response
from app.agents.generator import AgentGenerator
from app.agents.semantic_validator import SemanticValidator
from app import db
import random
import logging

logger = logging.getLogger(__name__)

class AgentSelector:
    """
    Selects next question to maximize information gain.
    Can use existing items OR generate adaptive questions dynamically.
    Now includes semantic validation and adaptive difficulty progression.
    """
    
    def __init__(self):
        self.generator = AgentGenerator()
        self.validator = SemanticValidator()
    
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
            # Analyze performance patterns for adaptive difficulty
            difficulty_analysis = self.validator.analyze_difficulty_progression(response_history)
            logger.info(f"[ADAPTIVE] Difficulty analysis: {difficulty_analysis}")
            
            # Select target competency with thematic clustering
            target_comp = self._select_target_competency_with_clustering(
                proficiency, 
                response_history
            )
            
            # Determine difficulty with progressive adaptation
            base_difficulty = self._determine_difficulty(proficiency.get(target_comp, {}))
            adapted_difficulty = self._adapt_difficulty_based_on_performance(
                base_difficulty, 
                difficulty_analysis
            )
            
            logger.info(f"[ADAPTIVE] Target: {target_comp} | Base: {base_difficulty} | Adapted: {adapted_difficulty}")
            
            # Get recent questions for semantic validation
            recent_questions = [r.get('stem', '') for r in response_history[-3:] if 'stem' in r]
            
            # Try to generate valid question (with retry logic)
            max_retries = 3
            for attempt in range(max_retries):
                generated_data = self.generator.generate_adaptive_question(
                    competency=target_comp,
                    current_score=proficiency.get(target_comp, {}).get('score', 50),
                    difficulty_target=adapted_difficulty,
                    response_history=response_history,
                    user_context=user_context
                )
                
                if not generated_data:
                    logger.error(f"[ADAPTIVE] Generation FAILED on attempt {attempt + 1}")
                    continue
                
                # Validate semantic distance
                semantic_validation = self.validator.validate_semantic_distance(
                    new_question=generated_data['stem'],
                    recent_questions=recent_questions,
                    competency=target_comp
                )
                
                logger.info(f"[ADAPTIVE] Semantic validation (attempt {attempt + 1}): {semantic_validation}")
                
                if not semantic_validation['valid']:
                    logger.warning(f"[ADAPTIVE] Question REJECTED (semantic): {semantic_validation['reason']}")
                    continue
                
                # Validate question quality (ambiguity, choice balance)
                quality_validation = self.validator.validate_question_quality(generated_data)
                
                logger.info(f"[ADAPTIVE] Quality validation (attempt {attempt + 1}): Score={quality_validation.get('quality_score', 0):.1f}")
                
                if quality_validation['valid']:
                    logger.info(f"[ADAPTIVE] ✅ Question passed ALL validations: {generated_data['stem'][:80]}...")
                    logger.info(f"[ADAPTIVE] Quality checks: {quality_validation.get('checks', [])}")
                    
                    # Create and save generated item with validation metadata
                    generated_item = Item(
                        stem=generated_data['stem'],
                        type=generated_data['type'],
                        competency=generated_data['competency'],
                        difficulty_b=generated_data['difficulty_b'],
                        discrimination_a=generated_data['discrimination_a'],
                        choices=generated_data.get('choices'),
                        answer_key=generated_data.get('answer_key'),
                        rubric=generated_data.get('rubric'),
                        tags=generated_data.get('tags', '') + ',validated,high_quality',
                        active=True
                    )
                    
                    # Store validation metadata
                    if 'metadata' not in generated_data:
                        generated_data['metadata'] = {}
                    generated_data['metadata']['quality_score'] = quality_validation.get('quality_score', 0)
                    generated_data['metadata']['semantic_score'] = semantic_validation.get('avg_similarity', 0)
                    
                    db.session.add(generated_item)
                    db.session.commit()
                    
                    logger.info(f"[ADAPTIVE] ✅ Created validated item ID {generated_item.id} (Quality: {quality_validation.get('quality_score', 0):.1f}/100)")
                    return generated_item
                else:
                    logger.warning(f"[ADAPTIVE] ❌ Question REJECTED (quality): {quality_validation['reason']}")
                    logger.warning(f"[ADAPTIVE] Quality details: {quality_validation.get('checks', [])}")
                    # Retry with different generation
                    continue
            
            # If all retries failed, fallback to existing items
            logger.error(f"[ADAPTIVE] All {max_retries} generation attempts failed validation")
            logger.info("[ADAPTIVE] 🔄 Graceful fallback: selecting from existing item bank")
            # Continue to fallback below (don't return None)
        
        # Fallback: Select best existing item from scored_items
        if scored_items:
            selected_item = scored_items[0][1]  # Highest scored item
            logger.info(f"[FALLBACK] Selected existing item ID {selected_item.id}: {selected_item.stem[:60]}...")
            return selected_item
        
        # No items available at all
        logger.error("[FALLBACK] No items available (neither generated nor existing)")
        return None
    
    def _should_generate_adaptive(
        self,
        proficiency: Dict[str, Any],
        response_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Decide if we should generate adaptive question vs. use existing.
        Prefers adaptive generation but allows graceful degradation.
        """
        # Try to generate adaptive questions when:
        # 1. We have enough history to personalize (2+ responses)
        # 2. User is making progress (not stuck on first questions)
        
        if len(response_history) < 2:
            # Use existing items for first few questions (baseline)
            logger.info("[ADAPTIVE] Using existing items for baseline (history < 2)")
            return False
        
        # After baseline, prefer adaptive generation
        # But system will fallback gracefully if generation fails
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
    
    def _select_target_competency_with_clustering(
        self,
        proficiency: Dict[str, Any],
        response_history: List[Dict[str, Any]]
    ) -> str:
        """
        Enhanced version with thematic clustering to avoid jarring topic jumps.
        Prioritizes competencies in same thematic cluster when appropriate.
        """
        # Get current thematic cluster
        recent_comps = [r.get('competency') for r in response_history[-4:] if 'competency' in r]
        recent_clusters = [self.validator.get_thematic_cluster(c) for c in recent_comps if c]
        
        current_cluster = recent_clusters[-1] if recent_clusters else None
        
        # Check if we should switch clusters
        should_switch = self.validator.should_switch_cluster(
            current_cluster=current_cluster,
            recent_clusters=recent_clusters,
            response_history=response_history
        ) if current_cluster else False
        
        logger.info(f"[CLUSTERING] Current: {current_cluster} | Should switch: {should_switch}")
        
        # Score competencies with cluster awareness
        comp_scores = []
        for comp, data in proficiency.items():
            score = 0.0
            comp_cluster = self.validator.get_thematic_cluster(comp)
            
            # Base scoring (uncertainty, coverage, recency)
            ci_width = data.get('ci_high', 80) - data.get('ci_low', 20)
            if ci_width > 25:
                score += 10.0
            elif ci_width > 15:
                score += 5.0
            
            if comp not in recent_comps:
                score += 8.0
            
            items_count = data.get('items_count', 0)
            if items_count < 2:
                score += 12.0
            elif items_count < 4:
                score += 6.0
            
            # Cluster-based bonus/penalty
            if current_cluster:
                if should_switch:
                    # Bonus for different cluster
                    if comp_cluster != current_cluster:
                        score += 15.0
                        logger.info(f"[CLUSTERING] {comp} gets switch bonus ({comp_cluster} != {current_cluster})")
                else:
                    # Bonus for same cluster (maintain coherence)
                    if comp_cluster == current_cluster:
                        score += 12.0
                        logger.info(f"[CLUSTERING] {comp} gets coherence bonus ({comp_cluster} == {current_cluster})")
            
            comp_scores.append((score, comp))
        
        if comp_scores:
            comp_scores.sort(reverse=True)
            top_comp = comp_scores[0][1]
            logger.info(f"[CLUSTERING] Selected: {top_comp} (cluster: {self.validator.get_thematic_cluster(top_comp)})")
            return top_comp
        
        # Fallback
        return list(proficiency.keys())[0] if proficiency else "Fundamentos de IA/ML & LLMs"
    
    def _adapt_difficulty_based_on_performance(
        self,
        base_difficulty: str,
        difficulty_analysis: Dict[str, Any]
    ) -> str:
        """
        Adjust difficulty based on recent performance patterns.
        """
        recommendation = difficulty_analysis.get('recommendation', 'same')
        
        difficulty_levels = ['easy', 'medium', 'hard']
        current_index = difficulty_levels.index(base_difficulty)
        
        if recommendation == 'harder' and current_index < 2:
            adapted = difficulty_levels[current_index + 1]
            logger.info(f"[ADAPTATION] Increasing difficulty: {base_difficulty} → {adapted}")
            return adapted
        elif recommendation == 'easier' and current_index > 0:
            adapted = difficulty_levels[current_index - 1]
            logger.info(f"[ADAPTATION] Decreasing difficulty: {base_difficulty} → {adapted}")
            return adapted
        else:
            logger.info(f"[ADAPTATION] Maintaining difficulty: {base_difficulty}")
            return base_difficulty
    
    def _determine_difficulty(self, comp_data: Dict[str, Any]) -> str:
        """
        Determine difficulty level for generated question based on user's score.
        Score ranges: 0-40 (easy), 40-70 (medium), 70-100 (hard)
        """
        score = comp_data.get('score', 50)
        
        if score < 40:
            return 'easy'
        elif score < 70:
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
        
        # Match difficulty to user level (theta scale converted to 0-100)
        # b=-1.0 → ~33, b=0.0 → 50, b=1.5 → ~75
        item_difficulty_score = 50 + (item.difficulty_b * 16.67)
        
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
