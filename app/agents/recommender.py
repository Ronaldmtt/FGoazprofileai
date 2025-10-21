from typing import Dict, Any, List
from app.core.scoring import IRTScorer

class AgentRecommender:
    """
    Generates personalized learning track recommendations.
    """
    
    def __init__(self):
        self.irt = IRTScorer()
    
    def generate_recommendations(self, proficiency: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate learning recommendations based on proficiency gaps.
        """
        global_score = self.irt.calculate_global_score(
            {k: v['score'] for k, v in proficiency.items()}
        )
        global_level = self.irt.calculate_level(global_score)
        
        gaps = []
        for competency, data in proficiency.items():
            score = data['score']
            level = self.irt.calculate_level(score)
            
            if score < 60:
                gaps.append({
                    'competency': competency,
                    'current_score': score,
                    'current_level': level,
                    'gap_severity': 60 - score
                })
        
        gaps.sort(key=lambda x: x['gap_severity'], reverse=True)
        
        tracks = []
        for gap in gaps[:3]:
            track = self._create_track(gap)
            tracks.append(track)
        
        return {
            'global_score': global_score,
            'global_level': global_level,
            'tracks': tracks,
            'summary': self._generate_summary(global_level, tracks)
        }
    
    def _create_track(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """Create learning track for a competency gap."""
        competency = gap['competency']
        current_level = gap['current_level']
        target_level = self._get_next_level(current_level)
        
        track_templates = {
            'Fundamentos de IA/ML & LLMs': {
                'title': 'Fundamentos de IA',
                'resources': [
                    'Curso: Introdução a LLMs e Modelos Generativos',
                    'Leitura: Artigos sobre arquitetura Transformer',
                    'Prática: Experimentar com APIs de LLMs'
                ]
            },
            'Ferramentas de IA no dia a dia': {
                'title': 'Ferramentas de IA',
                'resources': [
                    'Workshop: ChatGPT e Claude para produtividade',
                    'Prática: Integrar IA em workflows diários',
                    'Estudo de caso: Casos de uso por área'
                ]
            },
            'Prompt Engineering & Orquestração': {
                'title': 'Prompt Engineering',
                'resources': [
                    'Curso: Técnicas avançadas de prompting',
                    'Prática: Chain-of-thought e few-shot learning',
                    'Projeto: Criar sistema de prompts estruturados'
                ]
            },
            'Dados & Contextualização (RAG)': {
                'title': 'RAG e Contextualização',
                'resources': [
                    'Curso: Retrieval-Augmented Generation',
                    'Hands-on: Implementar pipeline RAG',
                    'Leitura: Vector databases e embeddings'
                ]
            },
            'Automação de Processos com IA': {
                'title': 'Automação com IA',
                'resources': [
                    'Workshop: Identificar processos automatizáveis',
                    'Prática: Criar workflows com IA',
                    'Projeto: Automatizar processo real'
                ]
            },
            'Ética, Segurança & Compliance': {
                'title': 'Ética e Segurança em IA',
                'resources': [
                    'Curso: LGPD e IA responsável',
                    'Leitura: Viés e fairness em modelos',
                    'Workshop: Auditoria e governança de IA'
                ]
            },
            'Produto e Negócio com IA': {
                'title': 'Produto e Negócio',
                'resources': [
                    'Curso: Product management para IA',
                    'Estudo de caso: ROI e métricas de IA',
                    'Workshop: Validação de features com IA'
                ]
            },
            'Code/No-code para IA': {
                'title': 'Desenvolvimento com IA',
                'resources': [
                    'Tutorial: Plataformas no-code (Zapier, Make)',
                    'Prática: Criar chatbot sem código',
                    'Projeto: Protótipo rápido com no-code'
                ]
            },
            'LLMOps & Qualidade': {
                'title': 'LLMOps e Qualidade',
                'resources': [
                    'Curso: Operacionalização de LLMs',
                    'Hands-on: Monitoring e logging',
                    'Prática: Versionamento de prompts'
                ]
            }
        }
        
        template = track_templates.get(competency, {
            'title': competency,
            'resources': [
                f'Desenvolver competência em {competency}',
                'Buscar cursos e materiais relevantes',
                'Praticar em projetos reais'
            ]
        })
        
        return {
            'competency': competency,
            'current_level': current_level,
            'target_level': target_level,
            'title': template['title'],
            'resources': template['resources']
        }
    
    def _get_next_level(self, current_level: str) -> str:
        """Get next proficiency level."""
        level_progression = ['N0', 'N1', 'N2', 'N3', 'N4', 'N5']
        try:
            idx = level_progression.index(current_level)
            return level_progression[min(idx + 1, len(level_progression) - 1)]
        except ValueError:
            return 'N1'
    
    def _generate_summary(self, global_level: str, tracks: List[Dict[str, Any]]) -> str:
        """Generate summary message."""
        level_messages = {
            'N0': 'Você está no início da jornada em IA. Foque em fundamentos!',
            'N1': 'Bom começo! Continue explorando ferramentas e conceitos básicos.',
            'N2': 'Conhecimento intermediário! Hora de aprofundar em áreas práticas.',
            'N3': 'Proficiência sólida! Busque especialização em áreas estratégicas.',
            'N4': 'Expertise avançada! Compartilhe conhecimento e lidere iniciativas.',
            'N5': 'Expert em IA! Você está no topo e pode mentorear outros.'
        }
        
        base_message = level_messages.get(global_level, 'Continue aprendendo!')
        
        if tracks:
            areas = ', '.join([t['competency'] for t in tracks[:2]])
            return f"{base_message} Recomendamos focar em: {areas}."
        
        return base_message
