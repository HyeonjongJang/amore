"""
Custom Persona Builder
Creates personalized personas from user selections, enriched with data-driven insights
from 62K+ crawled reviews and 8 customer segments.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


# Load persona profiles data
PERSONA_PROFILES_PATH = Path(__file__).parent.parent / "persona_profiles.json"

# Age group options
AGE_GROUPS = [
    "18-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50+"
]

# Gender options
GENDERS = ["여성", "남성"]

# Skin type options
SKIN_TYPES = [
    "건성",
    "지성",
    "복합성",
    "중성",
    "민감성"
]

# Skin concerns options (from review data)
SKIN_CONCERNS = [
    "보습",
    "주름/탄력",
    "미백/톤업",
    "모공",
    "트러블/여드름",
    "민감/진정",
    "피지관리",
    "각질",
    "다크서클",
    "자외선차단"
]

# Price sensitivity options
PRICE_SENSITIVITIES = [
    "낮음 (프리미엄 선호)",
    "중간",
    "높음 (가성비 중시)"
]

# Shopping frequency options
SHOPPING_FREQUENCIES = [
    "주 1회 이상",
    "월 2-3회",
    "월 1회",
    "분기 1회"
]


def load_persona_profiles() -> Dict[str, Any]:
    """Load data-driven persona profiles"""
    try:
        with open(PERSONA_PROFILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_segment_options() -> List[Dict[str, str]]:
    """Get list of available segments with descriptions"""
    profiles = load_persona_profiles()
    segments = []

    for segment_id, data in profiles.items():
        segments.append({
            "id": segment_id,
            "name_ko": data.get("name_ko", segment_id),
            "name_en": data.get("name_en", segment_id),
            "description": data.get("description", ""),
            "core_values": data.get("core_values", []),
            "review_count": data.get("data_driven_characteristics", {}).get("review_count", 0)
        })

    # Sort by review count (most popular first)
    segments.sort(key=lambda x: x["review_count"], reverse=True)
    return segments


def get_segment_insights(segment_id: str) -> Dict[str, Any]:
    """Get communication insights for a specific segment"""
    profiles = load_persona_profiles()

    if segment_id not in profiles:
        return {}

    segment = profiles[segment_id]
    characteristics = segment.get("data_driven_characteristics", {})
    communication = segment.get("communication_insights", {})

    return {
        "segment_id": segment_id,
        "name_ko": segment.get("name_ko"),
        "name_en": segment.get("name_en"),
        "description": segment.get("description"),
        "core_values": segment.get("core_values", []),
        "top_keywords": characteristics.get("top_keywords", [])[:10],
        "positive_triggers": characteristics.get("positive_triggers", []),
        "negative_triggers": characteristics.get("negative_triggers", []),
        "distinctive_keywords": characteristics.get("distinctive_keywords", [])[:10],
        "avg_rating": characteristics.get("avg_rating", 0),
        "review_count": characteristics.get("review_count", 0),
        "avg_review_length": characteristics.get("avg_review_length", 0),
        "sentiment_balance": communication.get("sentiment_balance", {}),
        "common_phrases": communication.get("common_phrases", {}),
        "sample_reviews": segment.get("sample_reviews", [])[:3]
    }


def build_custom_persona(
    name: str,
    age_group: str,
    gender: str,
    skin_type: str,
    skin_concerns: List[str],
    segment_id: str,
    price_sensitivity: str = "중간",
    shopping_frequency: str = "월 1회",
    preferred_brands: Optional[List[str]] = None,
    additional_notes: str = ""
) -> Dict[str, Any]:
    """
    Build a custom persona from user selections, enriched with segment insights.

    Args:
        name: Custom persona name
        age_group: Age range
        gender: Gender
        skin_type: Primary skin type
        skin_concerns: List of skin concerns
        segment_id: Selected customer segment ID
        price_sensitivity: Price sensitivity level
        shopping_frequency: How often they shop
        preferred_brands: Optional list of preferred brands
        additional_notes: Any additional context

    Returns:
        Complete persona dictionary compatible with existing agents
    """
    # Get segment insights
    segment_insights = get_segment_insights(segment_id)

    # Map price sensitivity to value
    price_map = {
        "낮음 (프리미엄 선호)": "낮음",
        "중간": "중간",
        "높음 (가성비 중시)": "높음"
    }

    # Build communication style based on segment
    comm_style = _build_communication_style(segment_id, segment_insights)

    # Build purchase triggers based on segment
    purchase_triggers = _build_purchase_triggers(segment_id, segment_insights)

    # Build lifestyle description
    lifestyle = _build_lifestyle(segment_id, segment_insights, shopping_frequency)

    # Build values based on segment
    values = segment_insights.get("core_values", [])

    # Build message keywords from segment
    message_keywords = segment_insights.get("distinctive_keywords", [])[:6]

    # Generate unique ID
    persona_id = f"CUSTOM_{segment_id.upper()[:3]}"

    persona = {
        "id": persona_id,
        "name": name,
        "name_en": f"Custom {segment_insights.get('name_en', 'Persona')}",
        "is_custom": True,
        "age_group": age_group,
        "gender": gender,
        "skin_type": skin_type,
        "skin_concerns": skin_concerns,
        "lifestyle": lifestyle,
        "shopping_pattern": {
            "frequency": shopping_frequency,
            "avg_purchase": _estimate_avg_purchase(price_sensitivity),
            "preferred_time": "저녁 9-11시",
            "channel": "모바일 앱"
        },
        "preferred_brands": preferred_brands or [],
        "price_sensitivity": price_map.get(price_sensitivity, price_sensitivity),
        "promotion_response": _get_promotion_response(segment_id),
        "communication_style": comm_style,
        "purchase_triggers": purchase_triggers,
        "pain_points": skin_concerns,
        "values": values,
        "message_keywords": message_keywords,
        # Data-driven enrichment
        "segment_data": {
            "segment_id": segment_id,
            "segment_name": segment_insights.get("name_ko"),
            "positive_triggers": segment_insights.get("positive_triggers", []),
            "negative_triggers": segment_insights.get("negative_triggers", []),
            "top_keywords": segment_insights.get("top_keywords", []),
            "common_phrases": segment_insights.get("common_phrases", {}),
            "sample_reviews": segment_insights.get("sample_reviews", [])
        },
        "additional_notes": additional_notes
    }

    return persona


def _build_communication_style(segment_id: str, insights: Dict) -> str:
    """Build communication style description based on segment"""
    styles = {
        "conscious_consumer": "신뢰감 있고 전문적인 정보 중심, 성분과 효능 강조",
        "high_end_hauler": "품격 있고 고급스러운 표현, 프리미엄 가치 강조",
        "diy_diva": "정보 공유형, 활용 팁 제공, 커스터마이징 어필",
        "wellness_warrior": "감성적이고 편안한 톤, 힐링과 케어 강조",
        "skinminimalist": "간결하고 핵심만, 효율성과 편리함 강조",
        "beautopian": "트렌디하고 활기찬 톤, SNS 감성, 즉각 효과 강조",
        "savvy_shopper": "혜택 명확히, 가격/할인 정보 중심, 실용적",
        "non_conformist": "독특하고 개성있는 표현, 특별함 강조"
    }
    return styles.get(segment_id, "친근하고 자연스러운 말투")


def _build_purchase_triggers(segment_id: str, insights: Dict) -> List[str]:
    """Build purchase triggers based on segment"""
    triggers = {
        "conscious_consumer": ["순한 성분", "저자극", "비건/친환경", "성분 정보"],
        "high_end_hauler": ["프리미엄", "선물용", "럭셔리 패키지", "한정판"],
        "diy_diva": ["레이어링", "믹스 활용", "커스터마이징", "부스팅"],
        "wellness_warrior": ["힐링", "진정", "마사지", "스파 경험"],
        "skinminimalist": ["올인원", "간편함", "시간절약", "다기능"],
        "beautopian": ["신상", "SNS 화제", "즉각 효과", "트렌드"],
        "savvy_shopper": ["할인", "세일", "가성비", "쿠폰/적립"],
        "non_conformist": ["새로운", "특별한", "독특한", "개성"]
    }
    return triggers.get(segment_id, insights.get("positive_triggers", [])[:4])


def _build_lifestyle(segment_id: str, insights: Dict, frequency: str) -> str:
    """Build lifestyle description based on segment"""
    lifestyles = {
        "conscious_consumer": "환경과 윤리적 소비에 관심, 성분을 꼼꼼히 확인하는 신중한 소비자",
        "high_end_hauler": "프리미엄 제품 선호, 선물용 구매 많음, 브랜드 가치 중시",
        "diy_diva": "다양한 제품 조합과 실험을 즐김, 뷰티 정보 공유 활발",
        "wellness_warrior": "마음챙김과 힐링 추구, 스킨케어를 자기관리의 일부로 인식",
        "skinminimalist": "바쁜 일상, 효율 중시, 복잡한 루틴보다 간편함 선호",
        "beautopian": "SNS 활발, 트렌드에 민감, 새로운 제품에 관심 많음",
        "savvy_shopper": "합리적 소비, 가격 비교 철저, 할인/혜택 정보에 민감",
        "non_conformist": "개성 추구, 남들과 다른 선택 선호, 독특한 제품에 관심"
    }
    base = lifestyles.get(segment_id, "스킨케어에 관심 많은 소비자")
    return f"{base}, 구매빈도: {frequency}"


def _estimate_avg_purchase(price_sensitivity: str) -> str:
    """Estimate average purchase amount based on price sensitivity"""
    estimates = {
        "낮음 (프리미엄 선호)": "15-30만원",
        "중간": "5-10만원",
        "높음 (가성비 중시)": "3-5만원"
    }
    return estimates.get(price_sensitivity, "5-10만원")


def _get_promotion_response(segment_id: str) -> str:
    """Get promotion response pattern based on segment"""
    responses = {
        "conscious_consumer": "친환경/비건 인증에 민감",
        "high_end_hauler": "럭셔리 선물세트/한정판에 민감",
        "diy_diva": "신제품 체험/샘플에 민감",
        "wellness_warrior": "힐링/스파 경험 프로모션에 민감",
        "skinminimalist": "올인원/세트 할인에 민감",
        "beautopian": "신상/트렌드 제품에 민감",
        "savvy_shopper": "할인/세일/적립에 매우 민감",
        "non_conformist": "한정판/콜라보에 민감"
    }
    return responses.get(segment_id, "프로모션에 관심")


def get_persona_preview(
    age_group: str,
    gender: str,
    skin_type: str,
    skin_concerns: List[str],
    segment_id: str,
    price_sensitivity: str
) -> Dict[str, Any]:
    """
    Get a preview of what the custom persona would look like
    without creating the full persona object.
    """
    segment_insights = get_segment_insights(segment_id)

    return {
        "segment_name": segment_insights.get("name_ko", segment_id),
        "core_values": segment_insights.get("core_values", []),
        "communication_style": _build_communication_style(segment_id, segment_insights),
        "purchase_triggers": _build_purchase_triggers(segment_id, segment_insights),
        "positive_keywords": segment_insights.get("positive_triggers", []),
        "avoid_keywords": segment_insights.get("negative_triggers", []),
        "sample_review": segment_insights.get("sample_reviews", [""])[0][:200] + "..." if segment_insights.get("sample_reviews") else "",
        "estimated_purchase": _estimate_avg_purchase(price_sensitivity)
    }
