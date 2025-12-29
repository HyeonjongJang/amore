"""
Product Matcher Agent
Uses RAG to find and recommend products matching persona and campaign
Supports both Legacy (P001-P007) and Kadence (K001-K008) persona formats.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "rag"))
from config import OPENAI_API_KEY, LLM_MODEL

# Import persona compatibility helper
try:
    from utils.persona_compat import get_skin_type
    COMPAT_AVAILABLE = True
except ImportError:
    COMPAT_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Import RAG components
try:
    from rag.retriever import ProductRetriever
except ImportError:
    from retriever import ProductRetriever

# Brand name mapping: Korean -> English (as stored in vector DB)
BRAND_KR_TO_EN = {
    "설화수": "Sulwhasoo",
    "라네즈": "LANEIGE",
    "이니스프리": "innisfree",
    "헤라": "HERA",
    "아이오페": "IOPE",
    "에뛰드": "ETUDE",
    "마몽드": "Mamonde",
    "프리메라": "Primera",
    "에스쁘아": "espoir",
    "에스트라": "AESTURA",
    "한율": "HANYUL",
    "일리윤": "ILLIYOON",
    "오딧세이": "ODYSSEY",
    "해피바스": "HAPPYBATH",
    "미장센": "mise-en-scene",
    "아윤채": "AYUNCHE",
}

# Reverse mapping: English -> Korean
BRAND_EN_TO_KR = {v: k for k, v in BRAND_KR_TO_EN.items()}


class ProductMatcherAgent:
    """Agent 2: Product Matcher - Uses RAG to find relevant products"""

    def __init__(
        self,
        retriever: Optional[ProductRetriever] = None,
        model_name: str = LLM_MODEL,
        temperature: float = 0.3
    ):
        self.retriever = retriever or ProductRetriever()
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_API_KEY
        )
        self._setup_prompt()

    def _setup_prompt(self):
        """Setup the product selection prompt"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 아모레퍼시픽의 제품 전문가입니다.
RAG로 검색된 제품들 중에서 페르소나와 캠페인에 가장 적합한 제품을 선정하고,
각 제품의 핵심 셀링 포인트를 추출해주세요.

제품 선정 시 고려사항:
1. 페르소나의 피부타입, 피부고민과의 적합성
2. 가격대와 페르소나의 가격민감도 매칭
3. 캠페인 목적과의 연관성
4. 시즌/이벤트와의 적합성

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "selected_products": [
        {{
            "product_name": "제품명",
            "brand": "브랜드",
            "price_krw": 가격,
            "key_selling_points": ["셀링포인트1", "셀링포인트2", "셀링포인트3"],
            "persona_fit_reason": "이 페르소나에게 적합한 이유",
            "message_hook": "이 제품을 활용한 메시지 훅 (한 문장)"
        }}
    ],
    "primary_product": "메인으로 추천할 제품명",
    "bundle_suggestion": "세트/번들 추천 아이디어 (있다면)",
    "promotion_angle": "프로모션 각도 제안"
}}"""),
            ("human", """
## 페르소나 분석 결과
{persona_analysis}

## 검색된 제품 목록
{retrieved_products}

## 캠페인 정보
- 캠페인 목적: {campaign_purpose}
- 시즌/이벤트: {season_event}
- 타겟 브랜드: {brand}

위 정보를 바탕으로 가장 적합한 제품을 선정하고 셀링 포인트를 추출해주세요.
최대 3개의 제품을 선정해주세요.
""")
        ])

    def match_products(
        self,
        persona: Dict[str, Any],
        persona_analysis: Dict[str, Any],
        campaign_purpose: str,
        brand: str,
        season_event: Optional[str] = None,
        top_k: int = 7
    ) -> Dict[str, Any]:
        """
        Find and select products matching the persona and campaign

        Args:
            persona: Customer persona dictionary
            persona_analysis: Results from PersonaAnalyzerAgent
            campaign_purpose: Purpose of the campaign
            brand: Target brand
            season_event: Optional season/event context
            top_k: Number of products to retrieve from RAG

        Returns:
            Dictionary containing selected products and recommendations
        """
        # Step 1: Retrieve products using RAG
        retrieved_products = self._retrieve_products(
            persona=persona,
            brand=brand,
            campaign_purpose=campaign_purpose,
            top_k=top_k
        )

        if not retrieved_products:
            return {
                "error": "No products found",
                "selected_products": [],
                "primary_product": None
            }

        # Step 2: Format retrieved products for LLM
        products_text = self._format_products(retrieved_products)

        # Step 3: Use LLM to select and analyze products (with retry)
        chain = self.prompt | self.llm

        result = None
        max_retries = 2

        for attempt in range(max_retries):
            response = chain.invoke({
                "persona_analysis": json.dumps(persona_analysis, ensure_ascii=False, indent=2),
                "retrieved_products": products_text,
                "campaign_purpose": campaign_purpose,
                "season_event": season_event or "일반",
                "brand": brand
            })

            # Parse response
            try:
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                result = json.loads(content.strip())

                # Check if we got valid products
                if result.get('selected_products') and len(result['selected_products']) > 0:
                    break  # Success, exit retry loop
                else:
                    print(f"[DEBUG] Attempt {attempt+1}: LLM returned empty products, retrying...")

            except json.JSONDecodeError as e:
                print(f"[DEBUG] Attempt {attempt+1}: JSON parse error: {e}")
                result = {
                    "raw_result": response.content,
                    "parse_error": True,
                    "selected_products": []
                }

        # Fallback: If LLM failed to select products, create from retrieved products
        if not result or not result.get('selected_products'):
            print("[DEBUG] Fallback: Creating products from RAG results")
            result = self._create_fallback_products(retrieved_products[:3], brand)

        # Add metadata
        result["total_retrieved"] = len(retrieved_products)
        result["brand_filter"] = brand

        # Add product URLs and image URLs to selected products
        product_url_map = {p['name']: p.get('product_url', '') for p in retrieved_products}
        product_image_map = {p['name']: p.get('image_url', '') for p in retrieved_products}
        for prod in result.get('selected_products', []):
            prod['product_url'] = product_url_map.get(prod.get('product_name'), '')
            prod['image_url'] = product_image_map.get(prod.get('product_name'), '')

        return result

    def _create_fallback_products(self, products: List[Dict], brand: str) -> Dict[str, Any]:
        """Create fallback product selection from RAG results"""
        selected = []
        seen_names = set()  # Track seen product names to avoid duplicates

        for p in products:
            product_name = p.get('name', '')
            # Skip duplicates
            if product_name in seen_names:
                continue
            seen_names.add(product_name)

            selected.append({
                "product_name": product_name,
                "brand": p.get('brand', brand),
                "price_krw": p.get('price_krw', 0),
                "key_selling_points": [
                    f"Recommended for your skin type",
                    f"Popular {p.get('category', 'product')}",
                    "Best seller"
                ],
                "persona_fit_reason": "Selected based on your profile and preferences",
                "message_hook": f"Discover {product_name or 'this amazing product'}!",
                "product_url": p.get('product_url', ''),
                "image_url": p.get('image_url', '')
            })

            # Stop after 3 unique products
            if len(selected) >= 3:
                break

        return {
            "selected_products": selected,
            "primary_product": selected[0]['product_name'] if selected else None,
            "bundle_suggestion": None,
            "promotion_angle": "Product recommendation based on your profile",
            "fallback_used": True
        }

    def _retrieve_products(
        self,
        persona: Dict[str, Any],
        brand: str,
        campaign_purpose: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve products using RAG retriever"""
        # Convert Korean brand name to English for vector store search
        brand_en = BRAND_KR_TO_EN.get(brand, brand)

        # Build search query based on persona and campaign
        query_parts = []

        # Add skin concerns
        if persona.get('skin_concerns'):
            query_parts.append(f"skin concerns: {', '.join(persona['skin_concerns'])}")

        # Add skin type (supports both Legacy and Kadence formats)
        if COMPAT_AVAILABLE:
            skin_type = get_skin_type(persona)
            if skin_type and skin_type != 'N/A':
                query_parts.append(f"skin type: {skin_type}")
        else:
            # Fallback: try direct access and demographics
            skin_type = persona.get('skin_type') or persona.get('demographics', {}).get('skin_type')
            if skin_type:
                query_parts.append(f"skin type: {skin_type}")

        # Add campaign purpose keywords
        campaign_keywords = {
            "신제품 런칭": "new product launch",
            "시즌 프로모션": "seasonal promotion sale",
            "할인/세일 안내": "discount sale promotion",
            "VIP 전용 혜택": "premium VIP exclusive",
            "재구매 유도": "repurchase bestseller",
            "휴면 고객 활성화": "popular bestseller",
            "생일 축하 쿠폰": "gift set special"
        }
        query_parts.append(campaign_keywords.get(campaign_purpose, campaign_purpose))

        # Add brand to query for better semantic matching
        query_parts.append(f"brand: {brand_en}")

        query = " | ".join(query_parts)

        # Search with brand filter (using English brand name)
        # Request more results to account for duplicates
        raw_products = self.retriever.retrieve_by_keywords(
            keywords=query,
            brand=brand_en,
            top_k=top_k * 2  # Get more to filter duplicates
        )

        # Deduplicate products by product_id
        products = []
        seen_ids = set()
        for p in raw_products:
            pid = p.get('product_id')
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                products.append(p)

        # If not enough results with brand filter, search without
        if len(products) < 3:
            additional = self.retriever.retrieve_for_persona(
                persona=persona,
                top_k=top_k
            )
            # Add non-duplicate products
            existing_ids = {p['product_id'] for p in products}
            for p in additional:
                if p['product_id'] not in existing_ids:
                    products.append(p)
                    if len(products) >= top_k:
                        break

        return products

    def _format_products(self, products: List[Dict[str, Any]]) -> str:
        """Format products list for LLM prompt"""
        formatted = []

        for i, p in enumerate(products, 1):
            lines = [
                f"[제품 {i}]",
                f"제품명: {p.get('name', 'N/A')}",
                f"브랜드: {p.get('brand', 'N/A')}",
                f"카테고리: {p.get('category', 'N/A')}",
                f"가격: {p.get('price_krw', 0):,}원",
            ]

            if p.get('has_promotion'):
                lines.append(f"프로모션: {p.get('discount_percent', 0)}% 할인 중")

            # Add content snippet (description)
            content = p.get('content', '')
            if 'Description:' in content:
                desc_start = content.find('Description:') + len('Description:')
                desc_end = content.find('\n', desc_start)
                if desc_end == -1:
                    desc_end = min(desc_start + 200, len(content))
                description = content[desc_start:desc_end].strip()[:200]
                lines.append(f"설명: {description}")

            formatted.append("\n".join(lines))

        return "\n\n".join(formatted)


# Test function
def test_product_matcher():
    """Test the product matcher agent"""
    import json
    from pathlib import Path

    # Load test data
    personas_path = Path(__file__).parent.parent / "data" / "personas" / "personas.json"
    with open(personas_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)['personas']

    test_persona = personas[0]  # 트렌드세터 지영

    # Mock persona analysis (normally from PersonaAnalyzerAgent)
    mock_analysis = {
        "persona_summary": "트렌디한 20대 후반 여성, SNS 활발하고 신제품에 민감",
        "purchase_motivations": ["트렌드 선점", "인플루언서 추천", "한정판 소유욕"],
        "emotional_triggers": ["특별함", "남들보다 빠른 정보"],
        "recommended_tone": "친근하고 트렌디한"
    }

    print("Testing ProductMatcherAgent...")
    print(f"Persona: {test_persona['name']}")
    print("-" * 50)

    agent = ProductMatcherAgent()
    result = agent.match_products(
        persona=test_persona,
        persona_analysis=mock_analysis,
        campaign_purpose="신제품 런칭",
        brand="HERA",
        season_event="봄 신상"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    test_product_matcher()
