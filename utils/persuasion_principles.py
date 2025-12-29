"""
Persuasion Principles Module for Kadence 8 Segments
Based on Cialdini's 6 Principles of Persuasion + Extended Cognitive Triggers

Reference:
- "LLM-Generated Ads: From Personalization Parity to Persuasion Superiority" (arXiv:2512.03373)
- Authority (63.0%), Consensus (62.5%), Cognition (56.5%), Scarcity (54.5%)

"""
from typing import Dict, List, Any, Optional


# Big Five Personality Traits Mapping for Kadence Personas
PERSONA_PERSONALITY_MAP = {
    # K001: 의식있는 소비자 예진 - 성분 중시, 민감피부, 신중한 소비
    "K001": {
        "openness": "medium",          # 신중함
        "conscientiousness": "high",   # 성분 꼼꼼히 확인
        "extraversion": "low",         # 내향적, 신중
        "agreeableness": "medium",
        "neuroticism": "high",         # 민감피부 걱정
        "primary_triggers": ["authority", "cognition"],
        "secondary_triggers": ["social_proof", "commitment"],
        "message_style": "신뢰감 있고 전문적인 정보 중심",
        "keywords": ["순한", "저자극", "민감피부", "진정", "피부장벽"]
    },
    # K002: 하이엔드 수집가 서현 - 선물용, 프리미엄, 향/패키징 중시
    "K002": {
        "openness": "medium",
        "conscientiousness": "high",   # 품격 중시
        "extraversion": "medium",
        "agreeableness": "high",       # 선물 좋아함
        "neuroticism": "low",
        "primary_triggers": ["scarcity", "liking"],
        "secondary_triggers": ["authority", "reciprocity"],
        "message_style": "품격 있고 격조 있는 표현",
        "keywords": ["선물", "프리미엄", "향기로운", "세트", "스페셜"]
    },
    # K003: 스킨미니멀리스트 지은 - 간편함, 효율, 시간절약
    "K003": {
        "openness": "low",             # 복잡한 것 싫음
        "conscientiousness": "medium",
        "extraversion": "low",         # 바쁨
        "agreeableness": "medium",
        "neuroticism": "low",
        "primary_triggers": ["cognition", "commitment"],
        "secondary_triggers": ["social_proof", "authority"],
        "message_style": "간결하고 핵심만",
        "keywords": ["간단", "편하게", "매일", "하나로", "꾸준히"]
    },
    # K004: DIY 디바 하늘 - 조합, 비교, 커스터마이징
    "K004": {
        "openness": "high",            # 다양한 시도
        "conscientiousness": "high",   # 꼼꼼한 비교
        "extraversion": "medium",
        "agreeableness": "high",       # 정보 공유
        "neuroticism": "medium",
        "primary_triggers": ["cognition", "novelty"],
        "secondary_triggers": ["social_proof", "reciprocity"],
        "message_style": "정보 공유형, 팁 제공",
        "keywords": ["조합", "레이어링", "활용", "믹스", "커스텀"]
    },
    # K005: 웰니스 전사 유나 - 힐링, 향, 감성적 경험
    "K005": {
        "openness": "high",            # 감각적 경험
        "conscientiousness": "medium",
        "extraversion": "low",         # 혼자만의 시간
        "agreeableness": "high",
        "neuroticism": "medium",
        "primary_triggers": ["liking", "cognition"],
        "secondary_triggers": ["authority", "commitment"],
        "message_style": "감성적이고 편안한 톤",
        "keywords": ["향", "힐링", "진정", "시원한", "편안한"]
    },
    # K006: 알뜰 쇼퍼 민지 - 세일, 할인, 가성비
    "K006": {
        "openness": "low",             # 검증된 것 선호
        "conscientiousness": "high",   # 철저한 계산
        "extraversion": "medium",
        "agreeableness": "medium",
        "neuroticism": "medium",
        "primary_triggers": ["scarcity", "reciprocity"],
        "secondary_triggers": ["social_proof", "commitment"],
        "message_style": "혜택 명확히, 숫자로 표현",
        "keywords": ["세일", "할인", "행사", "1+1", "사은품"]
    },
    # K007: 뷰토피안 소연 - 즉각 효과, 데일리, 화장 전
    "K007": {
        "openness": "medium",
        "conscientiousness": "medium",
        "extraversion": "medium",
        "agreeableness": "medium",
        "neuroticism": "medium",
        "primary_triggers": ["social_proof", "cognition"],
        "secondary_triggers": ["authority", "novelty"],
        "message_style": "효과 중심, 실용적",
        "keywords": ["촉촉", "진정", "데일리", "매일", "화장전"]
    },
    # K008: 비순응적 혁명가 재이 - 개성, 셀프기프팅, 유니크
    "K008": {
        "openness": "high",            # 개성 추구
        "conscientiousness": "medium",
        "extraversion": "medium",
        "agreeableness": "low",        # 비순응
        "neuroticism": "low",
        "primary_triggers": ["novelty", "liking"],
        "secondary_triggers": ["scarcity", "commitment"],
        "message_style": "개성 존중, 자기 표현 응원",
        "keywords": ["나에게", "선물", "색상", "피부톤", "발림성"]
    }
}

# Backward compatibility: Map old P-IDs to K-IDs
LEGACY_PERSONA_MAP = {
    "P001": "K007",  # 트렌드세터 지영 → 뷰토피안 소연
    "P002": "K003",  # 워킹맘 수진 → 스킨미니멀리스트 지은
    "P003": "K001",  # 스킨케어 덕후 민서 → 의식있는 소비자 예진
    "P004": "K002",  # 럭셔리 뷰티러버 현주 → 하이엔드 수집가 서현
    "P005": "K005",  # 내추럴 뷰티 소희 → 웰니스 전사 유나
    "P006": "K007",  # K-뷰티 입문자 Emily → 뷰토피안 소연
    "P007": "K003",  # 그루밍족 준호 → 스킨미니멀리스트 지은
}

# Default personality for unknown personas
DEFAULT_PERSONALITY = {
    "openness": "medium",
    "conscientiousness": "medium",
    "extraversion": "medium",
    "agreeableness": "medium",
    "neuroticism": "medium",
    "primary_triggers": ["authority", "social_proof"],
    "secondary_triggers": ["scarcity", "reciprocity"],
    "message_style": "친근하고 신뢰감 있는 톤",
    "keywords": ["촉촉", "보습", "피부", "케어", "추천"]
}


# Cialdini's 6 Principles + Extended Triggers
PERSUASION_PRINCIPLES = {
    "authority": {
        "name_ko": "권위",
        "description": "전문가, 연구 결과, 인증 등 신뢰할 수 있는 출처 활용",
        "phrases_ko": [
            "피부과 전문의 추천",
            "임상 테스트 완료",
            "전문가가 인정한",
            "더마 테스트 완료",
            "아모레퍼시픽 연구진이 개발한",
            "특허 성분 함유",
            "뷰티 에디터 강추"
        ],
        "phrases_formal": [
            "피부과학 연구를 통해 검증된",
            "전문가들이 신뢰하는",
            "과학적 근거로 입증된"
        ],
        "effectiveness": 63.0
    },
    "social_proof": {
        "name_ko": "사회적 증거",
        "description": "다른 사람들의 선택과 만족을 보여줌",
        "phrases_ko": [
            "누적 판매 100만개 돌파",
            "리뷰 평점 4.8점",
            "많은 고객이 선택한",
            "인스타 화제 제품",
            "뷰티 유튜버 강추템",
            "재구매율 1위",
            "완판 기록 제품"
        ],
        "phrases_formal": [
            "수많은 고객님께서 선택하신",
            "꾸준히 사랑받아온",
            "고객님들의 신뢰로 완성된"
        ],
        "effectiveness": 62.5
    },
    "scarcity": {
        "name_ko": "희소성",
        "description": "한정 수량, 기간 제한으로 긴급성 유발",
        "phrases_ko": [
            "한정 수량",
            "오늘만 특가",
            "마감 임박",
            "선착순",
            "단독 혜택",
            "VIP 전용",
            "시즌 한정"
        ],
        "phrases_formal": [
            "특별히 준비된 한정 수량",
            "고객님만을 위한 단독 혜택",
            "이 기회를 놓치지 마세요"
        ],
        "effectiveness": 54.5
    },
    "reciprocity": {
        "name_ko": "상호성",
        "description": "먼저 혜택을 제공하여 보답 심리 유발",
        "phrases_ko": [
            "지금 구매 시 사은품 증정",
            "무료 샘플 증정",
            "적립금 2배",
            "무료 배송",
            "추가 증정",
            "특별 선물",
            "감사 쿠폰 증정"
        ],
        "phrases_formal": [
            "감사의 마음을 담아 준비한",
            "고객님께 드리는 특별한 선물",
            "성원에 보답하는 마음으로"
        ],
        "effectiveness": 52.0
    },
    "commitment": {
        "name_ko": "일관성",
        "description": "이전 선택이나 가치관과의 일관성 강조",
        "phrases_ko": [
            "꾸준히 사용하면",
            "지속적인 관리로",
            "당신의 루틴에 추가",
            "평소 관심 가졌던",
            "이미 선택하신 고객님께",
            "지난번 구매하신 제품과 함께"
        ],
        "phrases_formal": [
            "늘 변함없이 추구하시는",
            "일관된 아름다움을 위해",
            "지속적인 관리의 완성"
        ],
        "effectiveness": 50.0
    },
    "liking": {
        "name_ko": "호감",
        "description": "친밀감, 유사성, 칭찬 등으로 호감 형성",
        "phrases_ko": [
            "당신을 위한",
            "특별한 당신에게",
            "눈부신 당신",
            "아름다운 당신의",
            "빛나는 하루를",
            "소중한 피부를 위해"
        ],
        "phrases_formal": [
            "고객님의 아름다움을 위해",
            "늘 빛나시는 고객님께",
            "품격 있는 당신을 위한"
        ],
        "effectiveness": 48.0
    },
    "cognition": {
        "name_ko": "인지적 설득",
        "description": "논리적 근거, 성분 정보, 효능 설명",
        "phrases_ko": [
            "세라마이드 함유로",
            "히알루론산이 수분 공급",
            "비타민C가 피부 톤을",
            "레티놀 성분이",
            "콜라겐 생성을 도와",
            "피부 장벽 강화"
        ],
        "phrases_formal": [
            "과학적으로 설계된 포뮬러",
            "유효 성분이 피부 깊숙이",
            "연구를 통해 최적화된"
        ],
        "effectiveness": 56.5
    },
    "novelty": {
        "name_ko": "신규성",
        "description": "새로운 것, 최신 트렌드 강조",
        "phrases_ko": [
            "NEW",
            "신제품 런칭",
            "새롭게 선보이는",
            "최신 기술",
            "2025 신상",
            "첫 출시",
            "업그레이드된"
        ],
        "phrases_formal": [
            "새롭게 탄생한",
            "최신 연구로 완성된",
            "진화된 포뮬러"
        ],
        "effectiveness": 55.0
    }
}


def _normalize_persona_id(persona_id: str) -> str:
    """Normalize persona ID to Kadence format (K001-K008)"""
    if persona_id.startswith("K"):
        return persona_id
    # Legacy mapping for P001-P007
    return LEGACY_PERSONA_MAP.get(persona_id, persona_id)


def get_persona_personality(persona_id: str) -> Dict[str, Any]:
    """Get Big Five personality mapping for persona"""
    normalized_id = _normalize_persona_id(persona_id)
    return PERSONA_PERSONALITY_MAP.get(normalized_id, DEFAULT_PERSONALITY)


def get_persuasion_triggers(persona_id: str) -> Dict[str, List[str]]:
    """Get primary and secondary persuasion triggers for persona"""
    personality = get_persona_personality(persona_id)
    return {
        "primary": personality.get("primary_triggers", ["authority", "social_proof"]),
        "secondary": personality.get("secondary_triggers", ["scarcity", "reciprocity"])
    }


def get_persona_keywords(persona_id: str) -> List[str]:
    """Get recommended keywords for persona"""
    personality = get_persona_personality(persona_id)
    return personality.get("keywords", ["촉촉", "보습", "피부"])


def get_message_style(persona_id: str) -> str:
    """Get recommended message style for persona"""
    personality = get_persona_personality(persona_id)
    return personality.get("message_style", "친근하고 신뢰감 있는 톤")


def get_persuasion_phrases(
    persona_id: str,
    brand_formality: str = "medium",
    season_event: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Get recommended persuasion phrases for persona and brand

    Args:
        persona_id: Persona ID (K001-K008 or legacy P001-P007)
        brand_formality: 'high' for 설화수, 'medium' for 라네즈, 'low' for casual brands
        season_event: Optional season/event context

    Returns:
        Dictionary with phrases and applied principles
    """
    triggers = get_persuasion_triggers(persona_id)
    keywords = get_persona_keywords(persona_id)

    result = {
        "primary_phrases": [],
        "secondary_phrases": [],
        "applied_principles": [],
        "persona_keywords": keywords
    }

    # Get phrases for primary triggers
    for trigger in triggers["primary"]:
        principle = PERSUASION_PRINCIPLES.get(trigger, {})
        if brand_formality == "high":
            phrases = principle.get("phrases_formal", [])
        else:
            phrases = principle.get("phrases_ko", [])

        result["primary_phrases"].extend(phrases[:3])
        result["applied_principles"].append({
            "principle": trigger,
            "name_ko": principle.get("name_ko", trigger),
            "effectiveness": principle.get("effectiveness", 50.0)
        })

    # Get phrases for secondary triggers
    for trigger in triggers["secondary"]:
        principle = PERSUASION_PRINCIPLES.get(trigger, {})
        if brand_formality == "high":
            phrases = principle.get("phrases_formal", [])
        else:
            phrases = principle.get("phrases_ko", [])

        result["secondary_phrases"].extend(phrases[:2])

    # Add season-specific phrases
    if season_event:
        season_phrases = _get_season_phrases(season_event, brand_formality)
        result["season_phrases"] = season_phrases

    return result


def _get_season_phrases(season_event: str, formality: str) -> List[str]:
    """Get season/event specific phrases"""
    season_map = {
        "겨울": ["건조한 겨울에도", "촉촉한 겨울나기", "겨울철 보습 필수템"],
        "여름": ["여름철 피지 관리", "끈적임 없이 촉촉하게", "여름에도 산뜻하게"],
        "환절기": ["환절기 피부 진정", "변화하는 계절에 맞춰", "환절기 필수 케어"],
        "봄": ["새 봄 새 피부", "봄맞이 피부 리셋", "새롭게 시작하는 봄"],
        "VIP": ["VIP 고객님만을 위한", "특별한 혜택", "프리미엄 고객 전용"],
        "신제품": ["새롭게 선보이는", "첫 런칭 특가", "신상 얼리버드 혜택"],
        "할인": ["놓치면 아쉬운 특가", "한정 기간 할인", "최대 할인 혜택"],
        "행사": ["아세페 특별 행사", "한정 기간 특가", "득템 기회"]
    }

    for key, phrases in season_map.items():
        if key in season_event:
            return phrases

    return []


def build_persuasion_prompt_section(
    persona_id: str,
    brand: str,
    campaign_purpose: str,
    season_event: Optional[str] = None,
    persona_data: Optional[Dict] = None
) -> str:
    """
    Build persuasion principles section for message generation prompt

    Args:
        persona_id: Persona ID (K001-K008 or legacy P001-P007)
        brand: Brand name
        campaign_purpose: Campaign purpose
        season_event: Optional season/event context
        persona_data: Optional full persona data from personas_kadence_enriched.json

    Returns:
        Formatted string to include in LLM prompt
    """
    # Determine brand formality
    high_formality_brands = ["설화수", "아모레퍼시픽", "헤라"]
    formality = "high" if brand in high_formality_brands else "medium"

    # Get persuasion data
    personality = get_persona_personality(persona_id)
    phrases = get_persuasion_phrases(persona_id, formality, season_event)
    message_style = get_message_style(persona_id)

    # Build prompt section
    lines = []
    lines.append("## 적용할 설득 원칙 (Persuasion Principles)")
    lines.append("")

    # Primary principles
    lines.append("### 핵심 설득 원칙 (우선 적용)")
    for principle in phrases["applied_principles"]:
        lines.append(f"- **{principle['name_ko']}** (효과: {principle['effectiveness']}%)")
    lines.append("")

    # Message style
    lines.append(f"### 메시지 스타일: {message_style}")
    lines.append("")

    # Persona keywords (from Kadence data)
    if phrases.get("persona_keywords"):
        lines.append("### 페르소나 핵심 키워드")
        lines.append(f"- {', '.join(phrases['persona_keywords'])}")
        lines.append("")

    # Use persona data if available
    if persona_data:
        comm_style = persona_data.get("communication_style", {})
        if comm_style.get("do"):
            lines.append("### DO (권장 표현)")
            for item in comm_style["do"][:3]:
                lines.append(f"- {item}")
            lines.append("")
        if comm_style.get("dont"):
            lines.append("### DON'T (피해야 할 표현)")
            for item in comm_style["dont"][:3]:
                lines.append(f"- ❌ {item}")
            lines.append("")

        # Purchase triggers
        if persona_data.get("purchase_triggers"):
            lines.append("### 구매 트리거 키워드")
            triggers = persona_data["purchase_triggers"][:6]
            lines.append(f"- {', '.join(triggers)}")
            lines.append("")

    # Recommended phrases
    lines.append("### 추천 표현")
    lines.append("**핵심 표현:**")
    for phrase in phrases["primary_phrases"][:5]:
        lines.append(f"- {phrase}")
    lines.append("")

    lines.append("**보조 표현:**")
    for phrase in phrases["secondary_phrases"][:4]:
        lines.append(f"- {phrase}")
    lines.append("")

    # Season phrases
    if phrases.get("season_phrases"):
        lines.append("**시즌 표현:**")
        for phrase in phrases["season_phrases"]:
            lines.append(f"- {phrase}")
        lines.append("")

    # Personality-based guidance
    lines.append("### 페르소나 성향 기반 가이드")
    if personality["openness"] == "high":
        lines.append("- 새로운 경험, 혁신적 성분, 트렌드 강조 효과적")
    if personality["conscientiousness"] == "high":
        lines.append("- 효과 검증, 성분 정보, 실용적 가치 강조 효과적")
    if personality["extraversion"] == "high":
        lines.append("- 사회적 인정, SNS 화제성, 트렌드 강조 효과적")
    if personality["agreeableness"] == "high":
        lines.append("- 감성적 어필, 선물/나눔, 환경/윤리 강조 효과적")
    if personality["neuroticism"] == "high":
        lines.append("- 안전성, 저자극, 테스트 완료 등 안심 요소 강조 효과적")
    if personality["openness"] == "low":
        lines.append("- 검증된 제품, 간단명료한 설명 선호")
    if personality["agreeableness"] == "low":
        lines.append("- 개성 존중, 차별화된 접근 필요")

    lines.append("")
    lines.append("---")
    lines.append("위 설득 원칙과 표현을 자연스럽게 메시지에 녹여주세요.")
    lines.append("강제로 모든 표현을 사용할 필요는 없으며, 자연스러운 흐름이 중요합니다.")

    return "\n".join(lines)


# Kadence segment-specific prompt enhancers
def get_segment_prompt_enhancement(segment_id: str) -> str:
    """Get segment-specific prompt enhancement"""
    enhancements = {
        "conscious_consumer": "성분 안전성과 저자극을 최우선으로 강조하세요. 과장된 표현은 피하고 신뢰할 수 있는 정보만 제공하세요.",
        "high_end_hauler": "프리미엄 경험과 선물 가치를 강조하세요. 향과 패키징의 고급스러움을 묘사하세요.",
        "skinminimalist": "간결하게! 핵심만 전달하세요. 복잡한 루틴 설명은 피하고 '하나로', '간편하게'를 강조하세요.",
        "diy_diva": "다른 제품과의 조합 팁, 활용법을 제안하세요. 커스터마이징 가능성을 강조하세요.",
        "wellness_warrior": "향과 사용 경험을 감성적으로 묘사하세요. 힐링, 릴렉싱 느낌을 전달하세요.",
        "savvy_shopper": "할인율, 사은품, 혜택을 명확한 숫자로 제시하세요. 가성비를 강조하세요.",
        "beautopian": "즉각적인 효과와 데일리 사용성을 강조하세요. 화장 전 사용법을 제안하세요.",
        "non_conformist": "개성과 자기표현을 응원하세요. '나에게 주는 선물' 컨셉을 활용하세요."
    }
    return enhancements.get(segment_id, "")
