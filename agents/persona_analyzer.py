"""
Persona Analyzer Agent
Analyzes customer persona to extract purchase motivations and communication insights
Supports both Legacy (P001-P007) and Kadence (K001-K008) persona formats.
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import get_openai_api_key, LLM_MODEL

try:
    from utils.persona_compat import (
        get_age_group, get_gender, get_skin_type,
        is_kadence_persona, get_segment_id, build_persona_summary
    )
    COMPAT_AVAILABLE = True
except ImportError:
    COMPAT_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


class PersonaAnalyzerAgent:
    """Agent 1: Persona Analyzer - Extracts insights from customer persona"""

    def __init__(self, model_name: str = LLM_MODEL, temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=get_openai_api_key()
        )
        self.output_parser = JsonOutputParser()
        self._setup_prompt()

    def _setup_prompt(self):
        """Setup the analysis prompt template"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 아모레퍼시픽의 고객 분석 전문가입니다.
주어진 고객 페르소나를 분석하여 CRM 마케팅 메시지 작성에 필요한 인사이트를 도출해주세요.

분석 시 다음 사항을 고려하세요:
1. 이 고객이 구매를 결정하는 핵심 동기는 무엇인가?
2. 어떤 감성적 포인트가 이 고객에게 어필할 것인가?
3. 피해야 할 표현이나 주제는 무엇인가?
4. 가장 효과적인 메시지 톤과 스타일은?

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "persona_summary": "페르소나 한 줄 요약",
    "purchase_motivations": ["핵심 구매 동기 1", "핵심 구매 동기 2", "핵심 구매 동기 3"],
    "emotional_triggers": ["감성적 어필 포인트 1", "감성적 어필 포인트 2"],
    "pain_points": ["해결해주고 싶은 고민 1", "해결해주고 싶은 고민 2"],
    "avoid_topics": ["피해야 할 표현/주제 1", "피해야 할 표현/주제 2"],
    "recommended_tone": "추천 메시지 톤 설명",
    "key_message_angles": ["메시지 각도 1", "메시지 각도 2"],
    "best_timing": "추천 발송 시간대",
    "urgency_level": "high/medium/low - 긴급성 메시지 적합도"
}}"""),
            ("human", """
## 페르소나 정보
{persona_info}

## 캠페인 정보
- 캠페인 목적: {campaign_purpose}
- 시즌/이벤트: {season_event}
- 타겟 브랜드: {brand}

위 정보를 바탕으로 이 페르소나에 대한 마케팅 인사이트를 분석해주세요.
""")
        ])

    def analyze(
        self,
        persona: Dict[str, Any],
        campaign_purpose: str,
        brand: str,
        season_event: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze persona and extract marketing insights

        Args:
            persona: Customer persona dictionary
            campaign_purpose: Purpose of the campaign
            brand: Target brand for the message
            season_event: Optional season or event context

        Returns:
            Dictionary containing persona analysis results
        """
        # Format persona info as readable text
        persona_text = self._format_persona(persona)

        # Create the chain
        chain = self.prompt | self.llm

        # Invoke
        response = chain.invoke({
            "persona_info": persona_text,
            "campaign_purpose": campaign_purpose,
            "season_event": season_event or "일반",
            "brand": brand
        })

        # Parse JSON response
        try:
            # Extract JSON from response content
            content = response.content
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            analysis = json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback: return raw analysis
            analysis = {
                "raw_analysis": response.content,
                "parse_error": True
            }

        # Add metadata
        analysis["persona_id"] = persona.get("id", "unknown")
        analysis["persona_name"] = persona.get("name", "unknown")
        analysis["analyzed_for_brand"] = brand
        analysis["campaign_purpose"] = campaign_purpose

        return analysis

    def _format_persona(self, persona: Dict[str, Any]) -> str:
        """Format persona dictionary into readable text (supports both Legacy and Kadence formats)"""
        lines = []

        # Use compatibility helper if available
        if COMPAT_AVAILABLE:
            lines.append(f"이름: {persona.get('name', 'N/A')}")
            lines.append(f"연령대: {get_age_group(persona)}")
            lines.append(f"성별: {get_gender(persona)}")
            lines.append(f"피부타입: {get_skin_type(persona)}")

            # Kadence-specific fields
            if is_kadence_persona(persona):
                segment_id = get_segment_id(persona)
                if segment_id:
                    lines.append(f"세그먼트: {segment_id}")
                segment_size = persona.get('segment_size', {})
                if segment_size:
                    lines.append(f"세그먼트 비율: {segment_size.get('percentage', 0)}%")
        else:
            # Fallback: try both direct and demographics access
            lines.append(f"이름: {persona.get('name', 'N/A')}")
            demographics = persona.get('demographics', {})
            lines.append(f"연령대: {persona.get('age_group') or demographics.get('age_group', 'N/A')}")
            lines.append(f"성별: {persona.get('gender') or demographics.get('gender', 'N/A')}")
            lines.append(f"피부타입: {persona.get('skin_type') or demographics.get('skin_type', 'N/A')}")

        if persona.get('skin_concerns'):
            lines.append(f"피부고민: {', '.join(persona['skin_concerns'])}")

        lines.append(f"라이프스타일: {persona.get('lifestyle', 'N/A')}")

        if persona.get('shopping_pattern'):
            sp = persona['shopping_pattern']
            if isinstance(sp, dict):
                lines.append(f"쇼핑패턴: {sp.get('frequency', '')}, 평균구매 {sp.get('avg_purchase', '')}")
                lines.append(f"선호시간: {sp.get('preferred_time', '')}, 채널: {sp.get('channel', '')}")
                # Kadence additional fields
                if sp.get('behavior'):
                    lines.append(f"쇼핑행동: {sp['behavior']}")
            else:
                lines.append(f"쇼핑패턴: {sp}")

        if persona.get('preferred_brands'):
            lines.append(f"선호브랜드: {', '.join(persona['preferred_brands'])}")

        # Kadence: preferred_products
        if persona.get('preferred_products'):
            lines.append(f"선호제품: {', '.join(persona['preferred_products'])}")

        lines.append(f"가격민감도: {persona.get('price_sensitivity', 'N/A')}")
        lines.append(f"프로모션반응: {persona.get('promotion_response', 'N/A')}")

        # communication_style can be dict (Kadence) or string (Legacy)
        comm_style = persona.get('communication_style', 'N/A')
        if isinstance(comm_style, dict):
            lines.append(f"커뮤니케이션 톤: {comm_style.get('tone', 'N/A')}")
            if comm_style.get('do'):
                lines.append(f"DO: {', '.join(comm_style['do'][:3])}")
            if comm_style.get('dont'):
                lines.append(f"DON'T: {', '.join(comm_style['dont'][:3])}")
        else:
            lines.append(f"커뮤니케이션스타일: {comm_style}")

        if persona.get('purchase_triggers'):
            lines.append(f"구매트리거: {', '.join(persona['purchase_triggers'])}")

        if persona.get('pain_points'):
            lines.append(f"페인포인트: {', '.join(persona['pain_points'])}")

        if persona.get('values'):
            lines.append(f"가치관: {', '.join(persona['values'])}")

        # Kadence: message_keywords
        if persona.get('message_keywords'):
            mk = persona['message_keywords']
            if isinstance(mk, dict):
                if mk.get('primary'):
                    lines.append(f"핵심키워드: {', '.join(mk['primary'])}")
                if mk.get('avoid'):
                    lines.append(f"회피키워드: {', '.join(mk['avoid'])}")

        # Kadence: sample_message
        if persona.get('sample_message'):
            lines.append(f"샘플메시지: {persona['sample_message']}")

        return "\n".join(lines)


# Test function
def test_persona_analyzer():
    """Test the persona analyzer agent"""
    import json
    from pathlib import Path

    # Load test persona
    personas_path = Path(__file__).parent.parent / "data" / "personas" / "personas.json"
    with open(personas_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)['personas']

    test_persona = personas[0]  # 트렌드세터 지영

    print("Testing PersonaAnalyzerAgent...")
    print(f"Persona: {test_persona['name']}")
    print("-" * 50)

    agent = PersonaAnalyzerAgent()
    result = agent.analyze(
        persona=test_persona,
        campaign_purpose="신제품 런칭",
        brand="헤라",
        season_event="봄 신상"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    test_persona_analyzer()
