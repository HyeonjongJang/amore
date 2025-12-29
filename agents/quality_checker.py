"""
Quality Checker Agent
Validates generated CRM messages and predicts performance
Supports both Legacy (P001-P007) and Kadence (K001-K008) persona formats.
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, LLM_MODEL, BRAND_TONES_PATH

# Import persona compatibility helper
try:
    from utils.persona_compat import get_age_group, get_skin_type
    COMPAT_AVAILABLE = True
except ImportError:
    COMPAT_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class QualityCheckerAgent:
    """Agent 4: Quality Checker - Validates messages and predicts performance"""

    def __init__(
        self,
        brand_tones: Optional[Dict] = None,
        model_name: str = LLM_MODEL,
        temperature: float = 0.1  # Low temperature for consistent evaluation
    ):
        self.brand_tones = brand_tones or self._load_brand_tones()
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_API_KEY
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
        """Setup the quality check prompt"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 CRM 메시지 품질 검증 전문가입니다.
생성된 메시지를 다음 기준으로 검증하고 점수를 매겨주세요.

## 검증 항목
1. **글자수 준수**: 제목 40자 이내, 본문 350자 이내 (필수)
2. **브랜드 톤앤매너 일치도** (1-10점)
3. **페르소나 적합도** (1-10점)
4. **감성적 표현 자연스러움** (1-10점)
5. **CTA 명확성** (1-10점)
6. **전체 완성도** (1-10점)

## 성과 예측
- 예상 클릭률 (CTR): 업계 평균 2-3% 기준
- 예상 전환율 (CVR): 업계 평균 0.5-1% 기준
- 예측 신뢰도: high/medium/low

## 평가 기준
- 9-10점: 즉시 사용 가능한 우수 메시지
- 7-8점: 약간의 수정으로 사용 가능
- 5-6점: 수정 필요
- 5점 미만: 재작성 권장

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "validation": {{
        "title_check": {{
            "char_count": 실제글자수,
            "limit": 40,
            "passed": true/false,
            "feedback": "피드백"
        }},
        "body_check": {{
            "char_count": 실제글자수,
            "limit": 350,
            "passed": true/false,
            "feedback": "피드백"
        }},
        "brand_tone_score": 점수,
        "brand_tone_feedback": "브랜드 톤 피드백",
        "persona_fit_score": 점수,
        "persona_fit_feedback": "페르소나 적합성 피드백",
        "naturalness_score": 점수,
        "naturalness_feedback": "자연스러움 피드백",
        "cta_clarity_score": 점수,
        "cta_feedback": "CTA 피드백",
        "overall_score": 전체점수
    }},
    "predicted_performance": {{
        "estimated_ctr": "N.N%",
        "estimated_cvr": "N.N%",
        "confidence": "high/medium/low",
        "performance_reasoning": "예측 근거"
    }},
    "improvement_suggestions": ["개선제안1", "개선제안2", "개선제안3"],
    "strengths": ["강점1", "강점2"],
    "recommended_send_time": "추천 발송 시간대",
    "final_verdict": "APPROVED/NEEDS_REVISION/REJECTED",
    "verdict_reason": "최종 판정 이유"
}}"""),
            ("human", """
## 생성된 메시지
### 제목
{title}

### 본문
{body}

### CTA
{cta}

## 타겟 페르소나
{persona_info}

## 브랜드 정보
브랜드: {brand}
{brand_tone}

## 캠페인 정보
- 목적: {campaign_purpose}
- 시즌/이벤트: {season_event}

위 메시지를 검증하고 품질 리포트를 작성해주세요.
""")
        ])

    def validate(
        self,
        generated_message: Dict[str, Any],
        persona: Dict[str, Any],
        brand: str,
        campaign_purpose: str,
        season_event: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate generated CRM message

        Args:
            generated_message: Message from MessageGeneratorAgent
            persona: Customer persona dictionary
            brand: Target brand name
            campaign_purpose: Campaign purpose
            season_event: Optional season/event

        Returns:
            Quality validation report
        """
        # Handle new product_messages structure
        product_messages = generated_message.get('product_messages', [])

        # If new structure, validate first product's main message for overall quality
        if product_messages:
            first_product = product_messages[0]
            main_msg = first_product.get('main_message', {})
        else:
            # Fallback to old structure for backward compatibility
            main_msg = generated_message.get('main_message', {})

        title = main_msg.get('title', '')
        body = main_msg.get('body', '')
        cta = main_msg.get('cta', '')

        # Get brand tone
        brand_tone = self._get_brand_tone(brand)
        brand_tone_text = self._format_brand_tone(brand_tone)

        # Format persona info
        persona_text = self._format_persona(persona)

        # Create chain
        chain = self.prompt | self.llm

        # Invoke
        response = chain.invoke({
            "title": title,
            "body": body,
            "cta": cta,
            "persona_info": persona_text,
            "brand": brand,
            "brand_tone": brand_tone_text,
            "campaign_purpose": campaign_purpose,
            "season_event": season_event or "일반"
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
                "parse_error": True
            }

        # Add actual character counts (ground truth)
        result['actual_counts'] = {
            'title_chars': len(title),
            'body_chars': len(body),
            'title_passed': len(title) <= 40,
            'body_passed': len(body) <= 350
        }

        # Add metadata
        result['validated_brand'] = brand
        result['validated_persona'] = persona.get('name')

        # Validate all product messages if present
        if product_messages:
            result['product_validations'] = self._validate_product_messages(product_messages)
        # Fallback: Validate A/B variants if present (old structure)
        elif 'ab_variant_1' in generated_message:
            result['ab_variants_validation'] = self._validate_ab_variants(
                generated_message, brand_tone
            )

        return result

    def _validate_ab_variants(
        self,
        generated_message: Dict[str, Any],
        brand_tone: Dict
    ) -> Dict[str, Any]:
        """Quick validation of A/B variants"""
        variants = {}

        for key in ['ab_variant_1', 'ab_variant_2']:
            if key in generated_message:
                variant = generated_message[key]
                title_len = len(variant.get('title', ''))
                body_len = len(variant.get('body', ''))

                variants[key] = {
                    'title_chars': title_len,
                    'body_chars': body_len,
                    'title_passed': title_len <= 40,
                    'body_passed': body_len <= 350
                }

        return variants

    def _validate_product_messages(
        self,
        product_messages: list
    ) -> list:
        """Validate all product messages (main + alternatives)"""
        validations = []

        for pm in product_messages:
            product_name = pm.get('product_name', 'Unknown')
            product_validation = {
                'product_name': product_name,
                'product_index': pm.get('product_index', 0),
                'messages': {}
            }

            # Validate main message
            if 'main_message' in pm:
                main = pm['main_message']
                title_len = len(main.get('title', ''))
                body_len = len(main.get('body', ''))
                product_validation['messages']['main'] = {
                    'title_chars': title_len,
                    'body_chars': body_len,
                    'title_passed': title_len <= 40,
                    'body_passed': body_len <= 350,
                    'angle': main.get('angle', '')
                }

            # Validate alternative 1
            if 'alternative_1' in pm:
                alt1 = pm['alternative_1']
                title_len = len(alt1.get('title', ''))
                body_len = len(alt1.get('body', ''))
                product_validation['messages']['alternative_1'] = {
                    'title_chars': title_len,
                    'body_chars': body_len,
                    'title_passed': title_len <= 40,
                    'body_passed': body_len <= 350,
                    'angle': alt1.get('angle', '')
                }

            # Validate alternative 2
            if 'alternative_2' in pm:
                alt2 = pm['alternative_2']
                title_len = len(alt2.get('title', ''))
                body_len = len(alt2.get('body', ''))
                product_validation['messages']['alternative_2'] = {
                    'title_chars': title_len,
                    'body_chars': body_len,
                    'title_passed': title_len <= 40,
                    'body_passed': body_len <= 350,
                    'angle': alt2.get('angle', '')
                }

            validations.append(product_validation)

        return validations

    def _get_brand_tone(self, brand: str) -> Dict[str, Any]:
        """Get brand tone info"""
        if brand in self.brand_tones:
            return self.brand_tones[brand]

        for kr_name, info in self.brand_tones.items():
            if info.get('brand_name_en', '').upper() == brand.upper():
                return info

        return {}

    def _format_brand_tone(self, brand_tone: Dict[str, Any]) -> str:
        """Format brand tone for prompt"""
        if not brand_tone:
            return "브랜드 톤 정보 없음"

        lines = []
        lines.append(f"톤: {brand_tone.get('tone', 'N/A')}")
        lines.append(f"보이스: {brand_tone.get('voice', 'N/A')}")

        if brand_tone.get('keywords'):
            lines.append(f"키워드: {', '.join(brand_tone['keywords'][:5])}")

        if brand_tone.get('avoid_words'):
            lines.append(f"피해야 할 표현: {', '.join(brand_tone['avoid_words'])}")

        style = brand_tone.get('style_guide', {})
        if style:
            lines.append(f"문장 종결: {', '.join(style.get('sentence_ending', []))}")
            lines.append(f"이모지 사용: {style.get('emoji_use', 'N/A')}")

        return "\n".join(lines)

    def _format_persona(self, persona: Dict[str, Any]) -> str:
        """Format persona for prompt (supports both Legacy and Kadence formats)"""
        lines = []
        lines.append(f"이름: {persona.get('name', 'N/A')}")

        # Use compatibility helper if available
        if COMPAT_AVAILABLE:
            lines.append(f"연령대: {get_age_group(persona)}")
            lines.append(f"피부타입: {get_skin_type(persona)}")
        else:
            # Fallback: try direct access and demographics
            demographics = persona.get('demographics', {})
            lines.append(f"연령대: {persona.get('age_group') or demographics.get('age_group', 'N/A')}")
            lines.append(f"피부타입: {persona.get('skin_type') or demographics.get('skin_type', 'N/A')}")

        # communication_style can be dict (Kadence) or string (Legacy)
        comm_style = persona.get('communication_style', 'N/A')
        if isinstance(comm_style, dict):
            lines.append(f"커뮤니케이션 톤: {comm_style.get('tone', 'N/A')}")
        else:
            lines.append(f"커뮤니케이션 스타일: {comm_style}")

        if persona.get('purchase_triggers'):
            lines.append(f"구매 트리거: {', '.join(persona['purchase_triggers'])}")

        if persona.get('values'):
            lines.append(f"가치관: {', '.join(persona['values'])}")

        return "\n".join(lines)

    def get_summary_score(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of validation scores"""
        validation = validation_result.get('validation', {})

        scores = {
            'brand_tone': validation.get('brand_tone_score', 0),
            'persona_fit': validation.get('persona_fit_score', 0),
            'naturalness': validation.get('naturalness_score', 0),
            'cta_clarity': validation.get('cta_clarity_score', 0),
            'overall': validation.get('overall_score', 0)
        }

        # Calculate average
        valid_scores = [s for s in scores.values() if isinstance(s, (int, float))]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

        return {
            'scores': scores,
            'average_score': round(avg_score, 1),
            'verdict': validation_result.get('final_verdict', 'UNKNOWN'),
            'char_limits_passed': (
                validation_result.get('actual_counts', {}).get('title_passed', False) and
                validation_result.get('actual_counts', {}).get('body_passed', False)
            )
        }


# Test function
def test_quality_checker():
    """Test the quality checker agent"""
    import json
    from pathlib import Path

    # Load test persona
    personas_path = Path(__file__).parent.parent / "data" / "personas" / "personas.json"
    with open(personas_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)['personas']

    test_persona = personas[0]

    # Mock generated message
    mock_message = {
        "main_message": {
            "title": "서울 잇걸들의 NEW 픽, 센슈얼 누드 밤 ✨",
            "body": "트렌드세터라면 이미 알고 있죠? 헤라의 NEW 센슈얼 누드 밤이 드디어 공개됐어요. 서울 감성 가득한 8가지 뉴 컬러로 당신만의 시크한 립 메이크업을 완성해보세요. 촉촉한 밤 제형이 입술에 은은한 광택을 더해 하루종일 생기있는 입술을 연출해드려요. 인플루언서들 사이에서 벌써 화제! 한정 수량이니 서두르세요.",
            "cta": "한정판 먼저 만나기"
        }
    }

    print("Testing QualityCheckerAgent...")
    print(f"Persona: {test_persona['name']}")
    print("-" * 50)

    agent = QualityCheckerAgent()
    result = agent.validate(
        generated_message=mock_message,
        persona=test_persona,
        brand="헤라",
        campaign_purpose="신제품 런칭",
        season_event="봄 신상"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Print summary
    summary = agent.get_summary_score(result)
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Average Score: {summary['average_score']}/10")
    print(f"Verdict: {summary['verdict']}")
    print(f"Char Limits Passed: {summary['char_limits_passed']}")

    return result


if __name__ == "__main__":
    test_quality_checker()
