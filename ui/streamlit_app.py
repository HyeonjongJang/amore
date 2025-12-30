"""
Streamlit UI for CRM Message Generation System
아모레퍼시픽 AI Innovation Challenge
"""
import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import CRMMessageGenerator
from config import PERSONAS_PATH, BRAND_TONES_PATH

# Import persona compatibility helper
try:
    from utils.persona_compat import get_age_group, get_gender, get_skin_type
    COMPAT_AVAILABLE = True
except ImportError:
    COMPAT_AVAILABLE = False

# Import custom persona builder
try:
    from utils.custom_persona_builder import (
        AGE_GROUPS, GENDERS, SKIN_TYPES, SKIN_CONCERNS, PRICE_SENSITIVITIES,
        get_segment_options, get_segment_insights, build_custom_persona,
        get_persona_preview
    )
    CUSTOM_PERSONA_AVAILABLE = True
except ImportError:
    CUSTOM_PERSONA_AVAILABLE = False

def _get_persona_age(persona):
    """Get age_group from persona (supports both formats)"""
    if COMPAT_AVAILABLE:
        return get_age_group(persona)
    return persona.get('age_group') or persona.get('demographics', {}).get('age_group', 'N/A')

def _get_persona_gender(persona):
    """Get gender from persona (supports both formats)"""
    if COMPAT_AVAILABLE:
        return get_gender(persona)
    return persona.get('gender') or persona.get('demographics', {}).get('gender', 'N/A')

def _get_persona_skin_type(persona):
    """Get skin_type from persona (supports both formats)"""
    if COMPAT_AVAILABLE:
        return get_skin_type(persona)
    return persona.get('skin_type') or persona.get('demographics', {}).get('skin_type', 'N/A')

def _get_comm_style(persona):
    """Get communication style (dict or string)"""
    cs = persona.get('communication_style', 'N/A')
    if isinstance(cs, dict):
        return cs.get('tone', 'N/A')
    return cs

# Page configuration
st.set_page_config(
    page_title="CRM 메시지 자동 생성 시스템",
    page_icon="💌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .message-box {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .title-preview {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .body-preview {
        font-size: 1rem;
        color: #333;
        line-height: 1.6;
    }
    .cta-button {
        background-color: #FF6B6B;
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        display: inline-block;
        margin-top: 1rem;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .brand-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(ttl=300)  # Cache for 5 minutes only
def load_generator():
    """Load the CRM generator (cached for 5 minutes)"""
    print("Creating new CRMMessageGenerator instance...")
    return CRMMessageGenerator()


@st.cache_data
def load_personas():
    """Load personas data"""
    with open(PERSONAS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['personas']


@st.cache_data
def load_brand_tones():
    """Load brand tones data"""
    with open(BRAND_TONES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['brands']


def get_score_class(score):
    """Get CSS class based on score"""
    if score >= 8:
        return "score-high"
    elif score >= 6:
        return "score-medium"
    return "score-low"


def get_brand_color(brand):
    """Get brand color"""
    colors = {
        "설화수": "#8B4513",
        "라네즈": "#4A90D9",
        "이니스프리": "#2E8B57",
        "헤라": "#1C1C1C",
        "아이오페": "#6B5B95",
        "에뛰드": "#FF69B4"
    }
    return colors.get(brand, "#666")


def render_custom_persona_builder():
    """Render the custom persona builder UI and return the built persona"""

    st.caption("62,000+ 리뷰 데이터 기반 맞춤 페르소나 생성")

    # Demographics section
    st.markdown("##### 인구통계")
    col1, col2 = st.columns(2)
    with col1:
        selected_age = st.selectbox(
            "연령대",
            options=AGE_GROUPS,
            index=1,  # Default to 25-29
            help="타겟 고객의 연령대"
        )
    with col2:
        selected_gender = st.selectbox(
            "성별",
            options=GENDERS,
            help="타겟 고객의 성별"
        )

    # Skin profile section
    st.markdown("##### 피부 프로필")
    selected_skin_type = st.selectbox(
        "피부 타입",
        options=SKIN_TYPES,
        index=2,  # Default to 복합성
        help="주요 피부 타입"
    )

    selected_concerns = st.multiselect(
        "피부 고민 (복수 선택)",
        options=SKIN_CONCERNS,
        default=["보습"],
        help="타겟 고객의 주요 피부 고민을 선택하세요"
    )

    # Customer segment section (data-driven)
    st.markdown("##### 고객 세그먼트")
    segments = get_segment_options()

    # Create segment options with descriptions
    segment_display = {
        f"{s['name_ko']} ({s['review_count']:,}명)": s['id']
        for s in segments
    }

    selected_segment_display = st.selectbox(
        "고객 유형",
        options=list(segment_display.keys()),
        help="62,000+ 리뷰에서 도출된 8가지 고객 세그먼트 중 선택"
    )
    selected_segment_id = segment_display[selected_segment_display]

    # Show segment insights
    segment_info = get_segment_insights(selected_segment_id)
    with st.expander("🔍 세그먼트 인사이트", expanded=False):
        st.markdown(f"**설명**: {segment_info.get('description', 'N/A')}")
        st.markdown(f"**핵심 가치**: {', '.join(segment_info.get('core_values', []))}")
        st.markdown(f"**긍정 트리거**: {', '.join(segment_info.get('positive_triggers', [])[:5])}")
        st.markdown(f"**부정 트리거**: {', '.join(segment_info.get('negative_triggers', [])[:5])}")
        st.markdown(f"**평균 평점**: {segment_info.get('avg_rating', 0):.2f}")

        # Show sample review
        samples = segment_info.get('sample_reviews', [])
        if samples:
            st.markdown("**샘플 리뷰**:")
            st.caption(samples[0][:150] + "..." if len(samples[0]) > 150 else samples[0])

    # Shopping behavior section
    st.markdown("##### 구매 행동")
    selected_price_sensitivity = st.selectbox(
        "가격 민감도",
        options=PRICE_SENSITIVITIES,
        index=1,  # Default to 중간
        help="가격에 대한 민감도"
    )

    # Build the custom persona (name auto-generated from segment)
    persona_name = f"맞춤 {segment_info.get('name_ko', '고객')}"
    custom_persona = build_custom_persona(
        name=persona_name,
        age_group=selected_age,
        gender=selected_gender,
        skin_type=selected_skin_type,
        skin_concerns=selected_concerns,
        segment_id=selected_segment_id,
        price_sensitivity=selected_price_sensitivity
    )

    # Show persona preview
    with st.expander("📋 생성된 페르소나 미리보기", expanded=True):
        st.markdown(f"**이름**: {custom_persona['name']}")
        st.markdown(f"**연령대**: {custom_persona['age_group']}")
        st.markdown(f"**성별**: {custom_persona['gender']}")
        st.markdown(f"**피부타입**: {custom_persona['skin_type']}")
        st.markdown(f"**피부고민**: {', '.join(custom_persona.get('skin_concerns', []))}")
        st.markdown(f"**고객 유형**: {segment_info.get('name_ko', 'N/A')}")
        st.markdown(f"**라이프스타일**: {custom_persona.get('lifestyle', 'N/A')}")
        st.markdown(f"**가격민감도**: {custom_persona.get('price_sensitivity', 'N/A')}")
        st.markdown(f"**구매트리거**: {', '.join(custom_persona.get('purchase_triggers', []))}")
        st.markdown(f"**커뮤니케이션**: {custom_persona.get('communication_style', 'N/A')}")

    return custom_persona


def main():
    # Header
    st.markdown('<p class="main-header">💌 CRM 메시지 자동 생성 시스템</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI Agent가 고객 페르소나에 맞는 개인화 마케팅 메시지를 생성합니다</p>', unsafe_allow_html=True)

    # Load resources
    generator = load_generator()
    personas = load_personas()
    brand_tones = load_brand_tones()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ 메시지 설정")

        # Persona selection
        st.subheader("1. 타겟 페르소나")

        # Toggle between predefined and custom persona
        persona_mode = st.radio(
            "페르소나 유형",
            options=["기존 페르소나", "맞춤 페르소나"],
            horizontal=True,
            help="기존 페르소나를 사용하거나 직접 맞춤 페르소나를 생성할 수 있습니다"
        )

        if persona_mode == "기존 페르소나":
            # Predefined persona selection
            persona_options = {f"{p['name']} ({_get_persona_age(p)})": p for p in personas}
            selected_persona_key = st.selectbox(
                "페르소나 선택",
                options=list(persona_options.keys()),
                help="타겟 고객 페르소나를 선택하세요"
            )
            selected_persona = persona_options[selected_persona_key]

            # Show persona details
            with st.expander("📋 페르소나 상세 정보", expanded=False):
                st.markdown(f"**이름**: {selected_persona['name']}")
                st.markdown(f"**연령대**: {_get_persona_age(selected_persona)}")
                st.markdown(f"**성별**: {_get_persona_gender(selected_persona)}")
                st.markdown(f"**피부타입**: {_get_persona_skin_type(selected_persona)}")
                st.markdown(f"**피부고민**: {', '.join(selected_persona.get('skin_concerns', []))}")
                st.markdown(f"**라이프스타일**: {selected_persona.get('lifestyle', 'N/A')}")
                st.markdown(f"**선호 브랜드**: {', '.join(selected_persona.get('preferred_brands', []))}")
                st.markdown(f"**가격민감도**: {selected_persona.get('price_sensitivity', 'N/A')}")
                st.markdown(f"**구매트리거**: {', '.join(selected_persona.get('purchase_triggers', []))}")
                st.markdown(f"**커뮤니케이션**: {_get_comm_style(selected_persona)}")

        else:
            # Custom persona builder
            if CUSTOM_PERSONA_AVAILABLE:
                selected_persona = render_custom_persona_builder()
            else:
                st.error("맞춤 페르소나 기능을 사용할 수 없습니다.")
                selected_persona = personas[0]  # Fallback

        st.divider()

        # Brand selection
        st.subheader("2. 브랜드 선택")
        brand_list = list(brand_tones.keys())
        selected_brand = st.selectbox(
            "브랜드",
            options=brand_list,
            help="메시지를 작성할 브랜드를 선택하세요"
        )

        # Show brand tone
        brand_info = brand_tones.get(selected_brand, {})
        with st.expander("🎨 브랜드 톤앤매너", expanded=False):
            st.markdown(f"**톤**: {brand_info.get('tone', 'N/A')}")
            st.markdown(f"**보이스**: {brand_info.get('voice', 'N/A')}")
            st.markdown(f"**키워드**: {', '.join(brand_info.get('keywords', [])[:5])}")
            st.markdown(f"**피해야 할 표현**: {', '.join(brand_info.get('avoid_words', [])[:3])}")

        st.divider()

        # Campaign settings
        st.subheader("3. 캠페인 설정")

        campaign_purposes = [
            "신제품 런칭",
            "시즌 프로모션",
            "할인/세일 안내",
            "VIP 전용 혜택",
            "재구매 유도",
            "휴면 고객 활성화",
            "생일 축하 쿠폰"
        ]
        selected_campaign = st.selectbox("캠페인 목적", campaign_purposes)

        season_events = [
            "일반",
            "봄 환절기 케어",
            "여름 자외선 케어",
            "가을 보습 준비",
            "겨울 보습 시즌",
            "설날",
            "발렌타인데이",
            "화이트데이",
            "어버이날",
            "블랙프라이데이",
            "연말 홀리데이"
        ]
        selected_season = st.selectbox("시즌/이벤트", season_events)

        st.divider()

        # Generate button
        generate_clicked = st.button(
            "🚀 메시지 생성",
            type="primary",
            width="stretch"
        )

    # Main content area
    if generate_clicked:
        with st.spinner("🤖 AI Agent가 메시지를 생성하고 있습니다..."):
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("1/4 페르소나 분석 중...")
            progress_bar.progress(25)

            # Generate message
            # For custom personas, pass the full object; for predefined, pass ID
            if selected_persona.get('is_custom'):
                persona_input = selected_persona
            else:
                persona_input = selected_persona['id']

            result = generator.generate(
                persona_id_or_name=persona_input,
                brand=selected_brand,
                campaign_purpose=selected_campaign,
                season_event=selected_season
            )

            status_text.text("2/4 제품 매칭 중...")
            progress_bar.progress(50)

            status_text.text("3/4 메시지 작성 중...")
            progress_bar.progress(75)

            status_text.text("4/4 품질 검증 중...")
            progress_bar.progress(100)

            status_text.empty()
            progress_bar.empty()

        if 'error' in result:
            st.error(f"오류가 발생했습니다: {result['error']}")
            return

        st.success("✅ 메시지 생성이 완료되었습니다!")

        # Store result in session state
        st.session_state['result'] = result

    # Display results if available
    if 'result' in st.session_state:
        result = st.session_state['result']

        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📨 생성된 메시지",
            "🛍️ 추천 제품",
            "🔍 상세 분석",
            "📊 품질 리포트"
        ])

        with tab1:
            display_messages(result)

        with tab2:
            display_products(result)

        with tab3:
            display_analysis(result)

        with tab4:
            display_quality_report(result)

        # Download section
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            st.download_button(
                label="📥 결과 JSON 다운로드",
                data=json.dumps(result, ensure_ascii=False, indent=2),
                file_name=f"crm_message_{selected_persona['name']}_{selected_brand}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                width="stretch"
            )


def display_messages(result):
    """Display generated messages - one per recommended product with expandable alternatives"""
    messages = result.get('messages', {})

    # Check for new product_messages structure
    product_messages = messages.get('product_messages', [])

    if product_messages:
        # New structure: display messages for each product
        st.subheader("📨 제품별 CRM 메시지")
        st.caption("각 추천 제품에 대한 메인 메시지와 대안 메시지입니다. 대안 버튼을 클릭하면 해당 메시지가 표시됩니다.")

        for idx, pm in enumerate(product_messages):
            product_name = pm.get('product_name', f'제품 {idx + 1}')
            product_index = pm.get('product_index', idx + 1)
            product_details = pm.get('product_details', {})

            # Product header with price info
            price = product_details.get('price_krw', 0)
            price_str = f" - {price:,}원" if price else ""

            st.markdown(f"### 🏷️ 제품 {product_index}: {product_name}{price_str}")

            # Main message section
            main_msg = pm.get('main_message', {})
            if main_msg:
                # Create columns: main content (left), char counts + alternative buttons (right)
                col_main, col_right = st.columns([3, 1])

                with col_main:
                    # Display main message
                    angle = main_msg.get('angle', '')
                    if angle:
                        st.caption(f"📐 어필 각도: {angle}")

                    st.markdown(f"""
                    <div class="message-box">
                        <div class="title-preview">{main_msg.get('title', '')}</div>
                        <div class="body-preview">{main_msg.get('body', '')}</div>
                        <div class="cta-button">{main_msg.get('cta', '자세히 보기')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_right:
                    # Character counts
                    title_len = len(main_msg.get('title', ''))
                    body_len = len(main_msg.get('body', ''))

                    st.metric("제목", f"{title_len}/40",
                             delta="OK" if title_len <= 40 else "초과",
                             delta_color="normal" if title_len <= 40 else "inverse")

                    st.metric("본문", f"{body_len}/350",
                             delta="OK" if body_len <= 350 else "초과",
                             delta_color="normal" if body_len <= 350 else "inverse")

                    st.markdown("---")
                    st.markdown("**대안 메시지**")

                # Alternative messages as expandable sections
                alt1 = pm.get('alternative_1', {})
                alt2 = pm.get('alternative_2', {})

                col_alt1, col_alt2 = st.columns(2)

                with col_alt1:
                    if alt1:
                        with st.expander(f"🔄 대안 1: {alt1.get('angle', '다른 어필')[:15]}...", expanded=False):
                            display_alternative_message(alt1, f"p{product_index}_alt1")

                with col_alt2:
                    if alt2:
                        with st.expander(f"🔄 대안 2: {alt2.get('angle', '또 다른 어필')[:15]}...", expanded=False):
                            display_alternative_message(alt2, f"p{product_index}_alt2")

            st.divider()

        # Overall strategy
        overall_strategy = messages.get('overall_strategy', '')
        if overall_strategy:
            st.info(f"💡 **전체 메시지 전략**: {overall_strategy}")

    else:
        # Fallback to old structure for backward compatibility
        display_messages_legacy(result)


def display_alternative_message(alt_msg: dict, key_prefix: str):
    """Display an alternative message in expanded view"""
    title = alt_msg.get('title', '')
    body = alt_msg.get('body', '')
    cta = alt_msg.get('cta', '')
    angle = alt_msg.get('angle', '')

    if angle:
        st.caption(f"📐 어필 각도: {angle}")

    # Character counts
    title_len = len(title)
    body_len = len(body)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**제목** ({title_len}/40자)")
    with col2:
        if title_len <= 40:
            st.success("OK", icon="✅")
        else:
            st.error("초과", icon="❌")

    st.info(title)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**본문** ({body_len}/350자)")
    with col2:
        if body_len <= 350:
            st.success("OK", icon="✅")
        else:
            st.error("초과", icon="❌")

    st.text_area("본문", body, height=120, disabled=True, key=f"{key_prefix}_body", label_visibility="collapsed")

    st.markdown(f"**CTA**: {cta}")


def display_messages_legacy(result):
    """Legacy display function for backward compatibility"""
    messages = result.get('messages', {})

    st.subheader("🏆 메인 메시지")

    if 'main_message' in messages:
        main_msg = messages['main_message']

        # Show which product the message is based on
        based_on = main_msg.get('based_on_product', '')
        if based_on:
            st.caption(f"🏷️ **기반 제품**: {based_on}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"""
            <div class="message-box">
                <div class="title-preview">{main_msg.get('title', '')}</div>
                <div class="body-preview">{main_msg.get('body', '')}</div>
                <div class="cta-button">{main_msg.get('cta', '자세히 보기')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            title_len = len(main_msg.get('title', ''))
            body_len = len(main_msg.get('body', ''))

            st.metric("제목 글자수", f"{title_len}/40",
                     delta="OK" if title_len <= 40 else "초과",
                     delta_color="normal" if title_len <= 40 else "inverse")

            st.metric("본문 글자수", f"{body_len}/350",
                     delta="OK" if body_len <= 350 else "초과",
                     delta_color="normal" if body_len <= 350 else "inverse")

    # A/B Variants
    st.subheader("🔄 A/B 테스트 대안")

    col_a, col_b = st.columns(2)

    with col_a:
        if 'ab_variant_1' in messages:
            v1 = messages['ab_variant_1']
            st.markdown("**Variant A**")
            based_on_a = v1.get('based_on_product', '')
            if based_on_a:
                st.caption(f"🏷️ 기반 제품: {based_on_a}")
            st.info(f"**제목**: {v1.get('title', '')}")
            st.text_area("본문 A", v1.get('body', ''), height=150, disabled=True, key="legacy_v1_body")
            st.caption(f"CTA: {v1.get('cta', '')}")

    with col_b:
        if 'ab_variant_2' in messages:
            v2 = messages['ab_variant_2']
            st.markdown("**Variant B**")
            based_on_b = v2.get('based_on_product', '')
            if based_on_b:
                st.caption(f"🏷️ 기반 제품: {based_on_b}")
            st.info(f"**제목**: {v2.get('title', '')}")
            st.text_area("본문 B", v2.get('body', ''), height=150, disabled=True, key="legacy_v2_body")
            st.caption(f"CTA: {v2.get('cta', '')}")


def display_quality_report(result):
    """Display quality report"""
    quality = result.get('quality_details', {})
    summary = result.get('quality_summary', {})

    # Summary metrics
    st.subheader("📈 품질 점수 요약")

    col1, col2, col3, col4 = st.columns(4)

    scores = summary.get('scores', {})

    with col1:
        score = scores.get('overall', 0)
        st.metric("전체 점수", f"{score}/10")

    with col2:
        score = scores.get('brand_tone', 0)
        st.metric("브랜드 톤", f"{score}/10")

    with col3:
        score = scores.get('persona_fit', 0)
        st.metric("페르소나 적합도", f"{score}/10")

    with col4:
        score = scores.get('naturalness', 0)
        st.metric("자연스러움", f"{score}/10")

    # Verdict
    verdict = summary.get('verdict', 'UNKNOWN')
    verdict_colors = {
        'APPROVED': '🟢',
        'NEEDS_REVISION': '🟡',
        'REJECTED': '🔴'
    }
    st.markdown(f"### 최종 판정: {verdict_colors.get(verdict, '⚪')} {verdict}")

    # Performance prediction
    st.subheader("📊 예상 성과")

    perf = quality.get('predicted_performance', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("예상 클릭률 (CTR)", perf.get('estimated_ctr', 'N/A'))

    with col2:
        st.metric("예상 전환율 (CVR)", perf.get('estimated_cvr', 'N/A'))

    with col3:
        confidence = perf.get('confidence', 'medium')
        conf_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🔴'}
        st.metric("예측 신뢰도", f"{conf_emoji.get(confidence, '⚪')} {confidence}")

    # Recommendations
    st.subheader("💡 추천 사항")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**강점**")
        strengths = quality.get('strengths', [])
        for s in strengths:
            st.markdown(f"✅ {s}")

    with col2:
        st.markdown("**개선 제안**")
        suggestions = quality.get('improvement_suggestions', [])
        for s in suggestions:
            st.markdown(f"💡 {s}")

    # Send time recommendation
    send_time = quality.get('recommended_send_time', '')
    if send_time:
        st.info(f"📅 **추천 발송 시간**: {send_time}")

    # Product-level validations (new structure)
    product_validations = quality.get('product_validations', [])
    if product_validations:
        st.subheader("📋 제품별 메시지 검증")

        for pv in product_validations:
            product_name = pv.get('product_name', 'Unknown')
            product_index = pv.get('product_index', 0)
            messages_val = pv.get('messages', {})

            with st.expander(f"제품 {product_index}: {product_name}", expanded=False):
                # Main message validation
                if 'main' in messages_val:
                    main_val = messages_val['main']
                    st.markdown("**메인 메시지**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        title_status = "✅" if main_val.get('title_passed') else "❌"
                        st.markdown(f"제목: {main_val.get('title_chars', 0)}/40자 {title_status}")
                    with col2:
                        body_status = "✅" if main_val.get('body_passed') else "❌"
                        st.markdown(f"본문: {main_val.get('body_chars', 0)}/350자 {body_status}")
                    with col3:
                        st.caption(f"어필: {main_val.get('angle', 'N/A')}")

                # Alternative 1 validation
                if 'alternative_1' in messages_val:
                    alt1_val = messages_val['alternative_1']
                    st.markdown("**대안 1**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        title_status = "✅" if alt1_val.get('title_passed') else "❌"
                        st.markdown(f"제목: {alt1_val.get('title_chars', 0)}/40자 {title_status}")
                    with col2:
                        body_status = "✅" if alt1_val.get('body_passed') else "❌"
                        st.markdown(f"본문: {alt1_val.get('body_chars', 0)}/350자 {body_status}")
                    with col3:
                        st.caption(f"어필: {alt1_val.get('angle', 'N/A')}")

                # Alternative 2 validation
                if 'alternative_2' in messages_val:
                    alt2_val = messages_val['alternative_2']
                    st.markdown("**대안 2**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        title_status = "✅" if alt2_val.get('title_passed') else "❌"
                        st.markdown(f"제목: {alt2_val.get('title_chars', 0)}/40자 {title_status}")
                    with col2:
                        body_status = "✅" if alt2_val.get('body_passed') else "❌"
                        st.markdown(f"본문: {alt2_val.get('body_chars', 0)}/350자 {body_status}")
                    with col3:
                        st.caption(f"어필: {alt2_val.get('angle', 'N/A')}")


def display_products(result):
    """Display recommended products with images"""
    products = result.get('recommended_products', [])

    st.subheader("🛍️ 추천 제품")

    if not products:
        st.info("추천 제품 정보가 없습니다.")
        return

    for i, prod in enumerate(products, 1):
        with st.expander(f"#{i} {prod.get('product_name', 'N/A')} - {prod.get('brand', '')}", expanded=(i==1)):
            # Layout: Image on left, details on right
            col_img, col_info = st.columns([1, 2])

            with col_img:
                # Display product image
                image_url = prod.get('image_url', '')
                if image_url:
                    try:
                        st.image(image_url, width="stretch")
                    except Exception:
                        st.markdown("🖼️ *이미지를 불러올 수 없습니다*")
                else:
                    st.markdown("""
                    <div style="background-color: #f0f0f0; height: 150px; display: flex;
                                align-items: center; justify-content: center; border-radius: 8px;">
                        <span style="color: #999;">이미지 없음</span>
                    </div>
                    """, unsafe_allow_html=True)

            with col_info:
                st.markdown(f"**브랜드**: {prod.get('brand', 'N/A')}")
                st.markdown(f"**가격**: {prod.get('price_krw', 0):,}원")

                if prod.get('key_selling_points'):
                    st.markdown("**셀링 포인트**:")
                    for point in prod['key_selling_points']:
                        st.markdown(f"  • {point}")

                if prod.get('persona_fit_reason'):
                    st.markdown(f"**적합 이유**: {prod['persona_fit_reason']}")

                if prod.get('product_url'):
                    st.link_button("🔗 제품 보기", prod['product_url'])


def display_analysis(result):
    """Display detailed analysis"""
    insights = result.get('persona_insights', {})

    st.subheader("🔍 페르소나 분석 인사이트")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**구매 동기**")
        motivations = insights.get('purchase_motivations', [])
        for m in motivations:
            st.markdown(f"🎯 {m}")

        st.markdown("**감성적 트리거**")
        triggers = insights.get('emotional_triggers', [])
        for t in triggers:
            st.markdown(f"💖 {t}")

    with col2:
        st.markdown("**메시지 각도**")
        angles = insights.get('key_message_angles', [])
        for a in angles:
            st.markdown(f"📝 {a}")

        st.markdown("**피해야 할 주제**")
        avoid = insights.get('avoid_topics', [])
        for a in avoid:
            st.markdown(f"⚠️ {a}")

    # Recommended tone
    tone = insights.get('recommended_tone', '')
    if tone:
        st.info(f"🎨 **추천 톤**: {tone}")

    # Raw JSON (collapsible)
    with st.expander("📄 전체 결과 JSON"):
        st.json(result)


if __name__ == "__main__":
    main()
