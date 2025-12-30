"""
Message Generator Agent
Generates personalized CRM messages with brand-specific tone and manner

Enhanced with:
- Persuasion Principles (Authority 63%, Consensus 62.5%, Cognition 56.5%, Scarcity 54.5%)
- Big Five Personality Mapping for Personas
- Reference: arXiv:2512.03373 "LLM-Generated Ads: From Personalization to Persuasion"
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import get_openai_api_key, LLM_MODEL, BRAND_TONES_PATH

# Import persuasion principles module
try:
    from utils.persuasion_principles import (
        build_persuasion_prompt_section,
        get_persona_personality,
        get_persuasion_triggers
    )
    PERSUASION_ENABLED = True
except ImportError:
    PERSUASION_ENABLED = False

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class MessageGeneratorAgent:
    """Agent 3: Message Generator - Creates CRM messages with brand tone"""

    def __init__(
        self,
        brand_tones: Optional[Dict] = None,
        model_name: str = LLM_MODEL,
        temperature: float = 0.7
    ):
        self.brand_tones = brand_tones or self._load_brand_tones()
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=get_openai_api_key()
        )
        self._setup_prompt()

    def _load_brand_tones(self) -> Dict:
        """Load brand tones from JSON file"""
        try:
            with open(BRAND_TONES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('brands', {})
        except FileNotFoundError:
            return {}

    def _setup_prompt(self):
        """Setup the message generation prompt"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 아모레퍼시픽의 CRM 카피라이터입니다.
주어진 정보를 바탕으로 각 추천 제품별로 고객 맞춤형 마케팅 메시지를 작성해주세요.

## 필수 규칙
1. **제목**: 정확히 40자 이내 (공백 포함)
2. **본문**: 정확히 350자 이내 (공백 포함)
3. 브랜드 톤앤매너 철저히 준수
4. 기계적이지 않은 자연스럽고 감성적인 표현
5. 명확한 CTA(Call-to-Action) 포함
6. 페르소나의 구매 동기와 감성 포인트 반영
7. **각 제품마다 서로 다른 각도와 어필 포인트로 메시지 작성**

## 좋은 CRM 메시지의 특징
- 첫 문장에서 관심 유도 (제목)
- 페르소나의 고민/니즈 공감
- 제품의 핵심 베네핏 명확히 전달
- 긴급성 또는 특별함 강조
- 자연스러운 행동 유도

## 🎯 설득 원칙 (Persuasion Principles) 적용 가이드
연구에 따르면 다음 원칙을 적용하면 설득력이 15-20% 향상됩니다:

1. **권위 (Authority)** - 전문가 추천, 임상 테스트, 특허 성분 언급
2. **사회적 증거 (Social Proof)** - 누적 판매량, 리뷰 평점, 재구매율
3. **희소성 (Scarcity)** - 한정 수량, 기간 한정, VIP 전용
4. **인지적 설득 (Cognition)** - 성분 효능, 과학적 근거 설명

각 페르소나에 맞는 설득 원칙이 별도로 제공됩니다.

## 중요: 각 제품별로 메시지 생성
- 추천 제품이 여러 개인 경우, 각 제품마다 별도의 메시지 세트를 작성해주세요.
- 각 제품에 대해 메인 메시지 1개 + 대안 메시지 2개를 작성합니다.
- 대안 메시지는 같은 제품에 대해 다른 각도로 어필하는 메시지입니다.

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "product_messages": [
        {{
            "product_name": "제품명",
            "product_index": 1,
            "main_message": {{
                "title": "메인 제목 (40자 이내)",
                "body": "메인 본문 (350자 이내)",
                "cta": "CTA 버튼 텍스트",
                "angle": "이 메시지의 어필 각도 (예: 효능 강조, 감성 어필, 트렌드 강조 등)"
            }},
            "alternative_1": {{
                "title": "대안 1 제목 (40자 이내)",
                "body": "대안 1 본문 (350자 이내)",
                "cta": "CTA",
                "angle": "대안 1의 어필 각도"
            }},
            "alternative_2": {{
                "title": "대안 2 제목 (40자 이내)",
                "body": "대안 2 본문 (350자 이내)",
                "cta": "CTA",
                "angle": "대안 2의 어필 각도"
            }}
        }}
    ],
    "overall_strategy": "전체 메시지 전략 설명"
}}"""),
            ("human", """
## 페르소나 정보
- 이름: {persona_name}
- 커뮤니케이션 스타일: {communication_style}
- 구매 트리거: {purchase_triggers}

## 페르소나 분석 결과
{persona_analysis}

## 추천 제품 정보 (각 제품별로 메시지 세트 생성 필요)
{product_info}

## 브랜드 톤앤매너
{brand_tone}

## 캠페인 정보
- 캠페인 목적: {campaign_purpose}
- 시즌/이벤트: {season_event}

{persuasion_section}

## 참고할 성공 CRM 메시지 예시
{crm_examples}

---
위 정보를 바탕으로 **각 추천 제품별로** 이 고객의 마음을 움직일 수 있는 CRM 메시지를 작성해주세요.
설득 원칙을 자연스럽게 녹여서 작성하되, 강제로 모든 표현을 사용할 필요는 없습니다.
각 제품당 메인 메시지 1개 + 대안 메시지 2개를 작성합니다.
제목은 반드시 40자 이내, 본문은 350자 이내로 작성하세요.
""")
        ])

    def generate(
        self,
        persona: Dict[str, Any],
        persona_analysis: Dict[str, Any],
        product_match: Dict[str, Any],
        brand: str,
        campaign_purpose: str,
        season_event: Optional[str] = None,
        crm_examples: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate CRM messages

        Args:
            persona: Customer persona dictionary
            persona_analysis: Results from PersonaAnalyzerAgent
            product_match: Results from ProductMatcherAgent
            brand: Target brand name
            campaign_purpose: Purpose of the campaign
            season_event: Optional season/event context
            crm_examples: Optional example CRM messages for reference

        Returns:
            Dictionary containing generated messages
        """
        # Get brand tone info
        brand_tone = self._get_brand_tone(brand)
        brand_tone_text = self._format_brand_tone(brand_tone)

        # Format product info
        product_text = self._format_product_info(product_match)

        # Build persuasion principles section (NEW)
        persuasion_section = ""
        if PERSUASION_ENABLED:
            persona_id = persona.get('id', '')
            persuasion_section = build_persuasion_prompt_section(
                persona_id=persona_id,
                brand=brand,
                campaign_purpose=campaign_purpose,
                season_event=season_event
            )

        # Create chain
        chain = self.prompt | self.llm

        # Invoke
        response = chain.invoke({
            "persona_name": persona.get('name', '고객'),
            "communication_style": persona.get('communication_style', '친근한'),
            "purchase_triggers": ', '.join(persona.get('purchase_triggers', [])),
            "persona_analysis": json.dumps(persona_analysis, ensure_ascii=False, indent=2),
            "product_info": product_text,
            "brand_tone": brand_tone_text,
            "campaign_purpose": campaign_purpose,
            "season_event": season_event or "일반",
            "persuasion_section": persuasion_section,
            "crm_examples": crm_examples or "없음"
        })

        # Parse response
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
        except json.JSONDecodeError:
            result = {
                "raw_result": response.content,
                "parse_error": True,
                "product_messages": []
            }

        # Add character counts for each product message
        if 'product_messages' in result:
            for pm in result['product_messages']:
                # Main message char counts
                if 'main_message' in pm:
                    pm['main_message']['title_char_count'] = len(pm['main_message'].get('title', ''))
                    pm['main_message']['body_char_count'] = len(pm['main_message'].get('body', ''))
                # Alternative 1 char counts
                if 'alternative_1' in pm:
                    pm['alternative_1']['title_char_count'] = len(pm['alternative_1'].get('title', ''))
                    pm['alternative_1']['body_char_count'] = len(pm['alternative_1'].get('body', ''))
                # Alternative 2 char counts
                if 'alternative_2' in pm:
                    pm['alternative_2']['title_char_count'] = len(pm['alternative_2'].get('title', ''))
                    pm['alternative_2']['body_char_count'] = len(pm['alternative_2'].get('body', ''))

        # Add metadata
        result['brand'] = brand
        result['persona_name'] = persona.get('name')
        result['campaign_purpose'] = campaign_purpose

        # Add product info from product_match to each message for reference
        selected_products = product_match.get('selected_products', [])
        if 'product_messages' in result:
            for i, pm in enumerate(result['product_messages']):
                if i < len(selected_products):
                    pm['product_details'] = {
                        'price_krw': selected_products[i].get('price_krw', 0),
                        'key_selling_points': selected_products[i].get('key_selling_points', []),
                        'product_url': selected_products[i].get('product_url', ''),
                        'image_url': selected_products[i].get('image_url', '')
                    }

        return result

    def _get_brand_tone(self, brand: str) -> Dict[str, Any]:
        """Get brand tone info, handling both Korean and English names"""
        # Direct lookup
        if brand in self.brand_tones:
            return self.brand_tones[brand]

        # Try to find by English name
        for kr_name, info in self.brand_tones.items():
            if info.get('brand_name_en', '').upper() == brand.upper():
                return info
            if info.get('brand_id', '').upper() == brand.upper():
                return info

        # Default to first brand or empty
        return self.brand_tones.get('라네즈', {})

    def _format_brand_tone(self, brand_tone: Dict[str, Any]) -> str:
        """Format brand tone info for prompt"""
        if not brand_tone:
            return "브랜드 톤 정보 없음"

        lines = []
        lines.append(f"브랜드: {brand_tone.get('brand_name_en', 'N/A')}")
        lines.append(f"컨셉: {brand_tone.get('brand_concept', 'N/A')}")
        lines.append(f"톤: {brand_tone.get('tone', 'N/A')}")
        lines.append(f"보이스: {brand_tone.get('voice', 'N/A')}")

        if brand_tone.get('keywords'):
            lines.append(f"키워드: {', '.join(brand_tone['keywords'][:6])}")

        if brand_tone.get('avoid_words'):
            lines.append(f"피해야 할 표현: {', '.join(brand_tone['avoid_words'])}")

        style = brand_tone.get('style_guide', {})
        if style:
            lines.append(f"문장 종결: {', '.join(style.get('sentence_ending', []))}")
            lines.append(f"격식: {style.get('formality', 'N/A')}")
            lines.append(f"이모지: {style.get('emoji_use', 'N/A')}")

        if brand_tone.get('example_phrases'):
            lines.append(f"예시 문구: {' / '.join(brand_tone['example_phrases'][:3])}")

        return "\n".join(lines)

    def _format_product_info(self, product_match: Dict[str, Any]) -> str:
        """Format product match info for prompt"""
        lines = []

        # Handle error or empty case
        if product_match.get('error') or not product_match:
            return """추천 제품 정보 없음
(브랜드의 대표 제품이나 신제품, 베스트셀러를 활용하여 메시지를 작성해주세요.
제품명을 직접 언급하지 않고 브랜드 특성과 효능 중심으로 작성해도 됩니다.)"""

        products = product_match.get('selected_products', [])
        primary = product_match.get('primary_product', '')

        if not products:
            return """추천 제품 정보 없음
(브랜드의 대표 제품이나 신제품, 베스트셀러를 활용하여 메시지를 작성해주세요.
제품명을 직접 언급하지 않고 브랜드 특성과 효능 중심으로 작성해도 됩니다.)"""

        if primary:
            lines.append(f"메인 추천 제품: {primary}")

        for i, prod in enumerate(products, 1):
            lines.append(f"\n[제품 {i}] {prod.get('product_name', 'N/A')}")
            lines.append(f"  브랜드: {prod.get('brand', 'N/A')}")
            lines.append(f"  가격: {prod.get('price_krw', 0):,}원")

            if prod.get('key_selling_points'):
                lines.append(f"  셀링포인트: {', '.join(prod['key_selling_points'])}")

            if prod.get('persona_fit_reason'):
                lines.append(f"  적합 이유: {prod['persona_fit_reason']}")

            if prod.get('message_hook'):
                lines.append(f"  메시지 훅: {prod['message_hook']}")

        if product_match.get('bundle_suggestion'):
            lines.append(f"\n번들 제안: {product_match['bundle_suggestion']}")

        if product_match.get('promotion_angle'):
            lines.append(f"프로모션 각도: {product_match['promotion_angle']}")

        return "\n".join(lines)


# Test function
def test_message_generator():
    """Test the message generator agent"""
    import json
    from pathlib import Path

    # Load test persona
    personas_path = Path(__file__).parent.parent / "data" / "personas" / "personas.json"
    with open(personas_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)['personas']

    test_persona = personas[0]  # 트렌드세터 지영

    # Mock data (normally from previous agents)
    mock_analysis = {
        "persona_summary": "트렌디한 20대 후반 여성",
        "purchase_motivations": ["트렌드 선점", "인플루언서 추천", "한정판"],
        "emotional_triggers": ["특별함", "남들보다 빠른"],
        "recommended_tone": "친근하고 트렌디한"
    }

    mock_product_match = {
        "selected_products": [
            {
                "product_name": "HERA 센슈얼 누드 밤",
                "brand": "HERA",
                "price_krw": 38000,
                "key_selling_points": ["촉촉한 발림성", "8가지 뉴 컬러", "서울 감성"],
                "persona_fit_reason": "트렌디한 컬러와 감성이 페르소나와 잘 맞음",
                "message_hook": "서울 잇걸들이 선택한 NEW 컬러"
            }
        ],
        "primary_product": "HERA 센슈얼 누드 밤",
        "promotion_angle": "한정판 신상 런칭"
    }

    print("Testing MessageGeneratorAgent...")
    print(f"Persona: {test_persona['name']}")
    print("-" * 50)

    agent = MessageGeneratorAgent()
    result = agent.generate(
        persona=test_persona,
        persona_analysis=mock_analysis,
        product_match=mock_product_match,
        brand="헤라",
        campaign_purpose="신제품 런칭",
        season_event="봄 신상"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    test_message_generator()
