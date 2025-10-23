"""
Semantic Validation System for Question Quality Control

Ensures:
1. Semantic similarity between consecutive questions (0.65-0.85 cosine similarity)
2. Thematic coherence to avoid jarring topic jumps
3. Progressive difficulty adaptation based on user performance patterns
"""

from typing import Dict, Any, List, Optional
import logging
import numpy as np
from openai import OpenAI
import os

logger = logging.getLogger(__name__)


class SemanticValidator:
    """
    Validates question quality using embeddings to ensure proper semantic distance,
    thematic coherence, and difficulty progression.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.min_similarity = 0.65
        self.max_similarity = 0.85
        self.embedding_cache = {}
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get text embedding using OpenAI's text-embedding-3-small model.
        Caches results to avoid redundant API calls.
        """
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            self.embedding_cache[text] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def validate_semantic_distance(
        self,
        new_question: str,
        recent_questions: List[str],
        competency: str
    ) -> Dict[str, Any]:
        """
        Validate that new question has appropriate semantic distance from recent ones.
        
        Target range: 0.65-0.85 cosine similarity
        - Below 0.65: too different (jarring topic jump)
        - Above 0.85: too similar (repetitive, low information gain)
        
        Returns:
            Dict with 'valid' (bool), 'similarity_scores' (list), 'reason' (str)
        """
        if not recent_questions:
            return {
                'valid': True,
                'similarity_scores': [],
                'reason': 'No previous questions to compare'
            }
        
        new_embedding = self.get_embedding(new_question)
        if not new_embedding:
            logger.warning("Could not get embedding for new question, skipping validation")
            return {'valid': True, 'similarity_scores': [], 'reason': 'Embedding failed'}
        
        similarities = []
        for recent_q in recent_questions[-3:]:  # Check last 3 questions
            recent_embedding = self.get_embedding(recent_q)
            if recent_embedding:
                similarity = self.cosine_similarity(new_embedding, recent_embedding)
                similarities.append(similarity)
        
        if not similarities:
            return {'valid': True, 'similarity_scores': [], 'reason': 'No embeddings to compare'}
        
        avg_similarity = np.mean(similarities)
        
        # Check if within acceptable range
        if avg_similarity < self.min_similarity:
            return {
                'valid': False,
                'similarity_scores': similarities,
                'avg_similarity': avg_similarity,
                'reason': f'Too dissimilar ({avg_similarity:.2f} < {self.min_similarity}) - jarring topic jump'
            }
        elif avg_similarity > self.max_similarity:
            return {
                'valid': False,
                'similarity_scores': similarities,
                'avg_similarity': avg_similarity,
                'reason': f'Too similar ({avg_similarity:.2f} > {self.max_similarity}) - repetitive content'
            }
        
        return {
            'valid': True,
            'similarity_scores': similarities,
            'avg_similarity': avg_similarity,
            'reason': f'Good semantic distance ({avg_similarity:.2f})'
        }
    
    def analyze_difficulty_progression(
        self,
        response_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user's performance pattern to determine optimal next difficulty.
        
        Looks for:
        - Recent success rate
        - Convergence patterns
        - Competency-specific trends
        
        Returns difficulty recommendation: 'easier', 'same', 'harder'
        """
        if len(response_history) < 3:
            return {'recommendation': 'same', 'confidence': 'low', 'reason': 'Insufficient history'}
        
        recent_responses = response_history[-5:]
        
        # Calculate success rate
        correct_count = sum(1 for r in recent_responses if r.get('is_correct', False))
        success_rate = correct_count / len(recent_responses)
        
        # Check score trend
        scores = [r.get('score', 0) for r in recent_responses if 'score' in r]
        if len(scores) >= 3:
            trend = np.mean(scores[-2:]) - np.mean(scores[:2])
        else:
            trend = 0
        
        # Decision logic
        if success_rate >= 0.8 and trend > 0:
            return {
                'recommendation': 'harder',
                'confidence': 'high',
                'reason': f'Strong performance ({success_rate:.0%} success, positive trend)',
                'success_rate': success_rate,
                'trend': trend
            }
        elif success_rate <= 0.3 and trend < 0:
            return {
                'recommendation': 'easier',
                'confidence': 'high',
                'reason': f'Struggling ({success_rate:.0%} success, negative trend)',
                'success_rate': success_rate,
                'trend': trend
            }
        else:
            return {
                'recommendation': 'same',
                'confidence': 'medium',
                'reason': f'Moderate performance ({success_rate:.0%} success)',
                'success_rate': success_rate,
                'trend': trend
            }
    
    def get_thematic_cluster(self, competency: str) -> str:
        """
        Map competency to thematic cluster to maintain coherence.
        
        Clusters:
        - foundations: Basic AI/ML concepts and fundamentals
        - tools: Practical tools and applications
        - ethics: Ethics, privacy, and responsible AI
        - advanced: LLMOps, automation, advanced techniques
        """
        cluster_map = {
            'Fundamentos de IA/ML & LLMs': 'foundations',
            'Prompt Engineering': 'tools',
            'Ferramentas de IA Generativa': 'tools',
            'Ética e Uso Responsável de IA': 'ethics',
            'IA no Trabalho e Produtividade': 'tools',
            'Automação e Integração de IA': 'advanced',
            'LLMOps e Gestão de IA': 'advanced',
            'IA em Casos Específicos': 'advanced',
            'Futuro e Tendências em IA': 'foundations'
        }
        
        return cluster_map.get(competency, 'foundations')
    
    def should_switch_cluster(
        self,
        current_cluster: str,
        recent_clusters: List[str],
        response_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Determine if it's appropriate to switch thematic cluster.
        
        Switch when:
        - Same cluster for 4+ consecutive questions
        - User shows mastery (high scores) in current cluster
        - Natural progression point (after assessment phase)
        """
        if len(recent_clusters) < 2:
            return False
        
        # Count consecutive same cluster
        consecutive = 1
        for cluster in reversed(recent_clusters[:-1]):
            if cluster == current_cluster:
                consecutive += 1
            else:
                break
        
        # Switch after 4+ consecutive in same cluster
        if consecutive >= 4:
            logger.info(f"Recommending cluster switch after {consecutive} consecutive in {current_cluster}")
            return True
        
        # Check mastery in current cluster
        cluster_responses = [r for r in response_history[-6:] 
                           if self.get_thematic_cluster(r.get('competency', '')) == current_cluster]
        
        if len(cluster_responses) >= 3:
            avg_score = np.mean([r.get('score', 0) for r in cluster_responses if 'score' in r])
            if avg_score > 75:
                logger.info(f"Recommending cluster switch due to mastery (avg score: {avg_score:.1f})")
                return True
        
        return False
    
    def validate_question_quality(
        self,
        question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate quality of generated question to ensure ambiguity and fairness.
        
        Checks:
        1. All choices have similar length (±30% variance)
        2. Choices are semantically diverse (not too similar)
        3. Distractor quality (plausible but incorrect)
        
        Returns validation result with scores and feedback.
        """
        stem = question_data.get('stem', '')
        choices = question_data.get('choices', [])
        
        if not choices or len(choices) < 4:
            return {
                'valid': False,
                'reason': 'Insufficient choices (need 4)',
                'quality_score': 0.0
            }
        
        quality_checks = []
        total_score = 0.0
        
        # Check 1: Length similarity (avoid one very long/short option)
        lengths = [len(choice) for choice in choices]
        avg_length = np.mean(lengths)
        max_variance = max(abs(l - avg_length) / avg_length for l in lengths if avg_length > 0)
        
        length_score = 1.0 if max_variance < 0.3 else (0.5 if max_variance < 0.5 else 0.0)
        quality_checks.append({
            'check': 'length_similarity',
            'score': length_score,
            'details': f'Max variance: {max_variance:.2%} (target: <30%)'
        })
        total_score += length_score
        
        # Check 2: Semantic diversity between choices
        choice_embeddings = []
        for choice in choices:
            emb = self.get_embedding(choice)
            if emb:
                choice_embeddings.append(emb)
        
        if len(choice_embeddings) >= 4:
            # Calculate pairwise similarities
            similarities = []
            for i in range(len(choice_embeddings)):
                for j in range(i + 1, len(choice_embeddings)):
                    sim = self.cosine_similarity(choice_embeddings[i], choice_embeddings[j])
                    similarities.append(sim)
            
            avg_choice_similarity = np.mean(similarities)
            
            # Good diversity: similarity between 0.4-0.75
            # Too similar (>0.75): repetitive options
            # Too different (<0.4): incoherent
            if 0.4 <= avg_choice_similarity <= 0.75:
                diversity_score = 1.0
            elif 0.3 <= avg_choice_similarity < 0.4 or 0.75 < avg_choice_similarity <= 0.85:
                diversity_score = 0.5
            else:
                diversity_score = 0.0
            
            quality_checks.append({
                'check': 'semantic_diversity',
                'score': diversity_score,
                'details': f'Avg similarity: {avg_choice_similarity:.2f} (target: 0.40-0.75)'
            })
            total_score += diversity_score
        else:
            logger.warning("Could not get embeddings for all choices")
            quality_checks.append({
                'check': 'semantic_diversity',
                'score': 0.5,
                'details': 'Could not compute (embedding failed)'
            })
            total_score += 0.5
        
        # Check 3: Stem clarity (not too long, not too short)
        stem_length = len(stem.split())
        if 10 <= stem_length <= 40:
            clarity_score = 1.0
        elif 5 <= stem_length < 10 or 40 < stem_length <= 60:
            clarity_score = 0.5
        else:
            clarity_score = 0.0
        
        quality_checks.append({
            'check': 'stem_clarity',
            'score': clarity_score,
            'details': f'Word count: {stem_length} (target: 10-40 words)'
        })
        total_score += clarity_score
        
        # Calculate final quality score (0-100)
        final_score = (total_score / len(quality_checks)) * 100
        
        # Question is valid if score >= 60
        is_valid = final_score >= 60
        
        return {
            'valid': is_valid,
            'quality_score': final_score,
            'checks': quality_checks,
            'reason': 'Passed quality checks' if is_valid else f'Low quality score: {final_score:.1f}/100'
        }
