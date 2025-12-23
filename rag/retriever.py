"""
Product Retriever Module
Handles persona-based product search using RAG
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))
from config import TOP_K_RESULTS, BRAND_NAME_MAPPING

try:
    from .vector_store import ProductVectorStore
except ImportError:
    from vector_store import ProductVectorStore


class ProductRetriever:
    """Retriever for persona-based product recommendations"""

    def __init__(self, vector_store: Optional[ProductVectorStore] = None):
        self.vector_store = vector_store or ProductVectorStore()
        # Ensure vector store is loaded
        if self.vector_store.vector_store is None:
            self.vector_store.build_vector_store()

    def _build_persona_query(self, persona: Dict[str, Any]) -> str:
        """Build a search query from persona attributes"""
        query_parts = []

        # Skin type
        if persona.get("skin_type"):
            query_parts.append(f"skin type: {persona['skin_type']}")

        # Skin concerns
        if persona.get("skin_concerns"):
            concerns = persona["skin_concerns"]
            if isinstance(concerns, list):
                concerns = ", ".join(concerns)
            query_parts.append(f"skin concerns: {concerns}")

        # Preferred brands
        if persona.get("preferred_brands"):
            brands = persona["preferred_brands"]
            if isinstance(brands, list):
                brands = ", ".join(brands)
            query_parts.append(f"brands: {brands}")

        # Price sensitivity / budget
        if persona.get("shopping_pattern", {}).get("avg_purchase"):
            query_parts.append(f"budget: {persona['shopping_pattern']['avg_purchase']}")

        # Purchase triggers (what motivates them)
        if persona.get("purchase_triggers"):
            triggers = persona["purchase_triggers"]
            if isinstance(triggers, list):
                triggers = ", ".join(triggers)
            query_parts.append(f"looking for: {triggers}")

        # Lifestyle considerations
        if persona.get("lifestyle"):
            query_parts.append(f"lifestyle: {persona['lifestyle']}")

        return " | ".join(query_parts)

    def _build_brand_filter(self, brands: List[str]) -> Optional[Dict]:
        """Build a filter for specific brands"""
        if not brands:
            return None

        # Normalize brand names
        normalized_brands = []
        for brand in brands:
            # Check if it's a Korean brand name that needs mapping
            for eng, kr in BRAND_NAME_MAPPING.items():
                if brand == kr:
                    normalized_brands.append(eng)
                    break
            else:
                normalized_brands.append(brand)

        if len(normalized_brands) == 1:
            return {"brand": normalized_brands[0]}
        else:
            return {"brand": {"$in": normalized_brands}}

    def retrieve_for_persona(
        self,
        persona: Dict[str, Any],
        top_k: int = TOP_K_RESULTS,
        filter_by_brand: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products matching a persona's profile

        Args:
            persona: Persona dictionary with attributes
            top_k: Number of results to return
            filter_by_brand: Whether to filter by preferred brands

        Returns:
            List of product dictionaries with relevance info
        """
        # Build search query
        query = self._build_persona_query(persona)

        # Build optional brand filter
        brand_filter = None
        if filter_by_brand and persona.get("preferred_brands"):
            brand_filter = self._build_brand_filter(persona["preferred_brands"])

        # Search
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter_dict=brand_filter
        )

        # Format results
        products = []
        for doc, score in results:
            product = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(1 - score),  # Convert distance to similarity
                "product_id": doc.metadata.get("product_id"),
                "name": doc.metadata.get("name"),
                "brand": doc.metadata.get("brand"),
                "brand_kr": doc.metadata.get("brand_kr"),
                "category": doc.metadata.get("category"),
                "price_krw": doc.metadata.get("price_krw"),
                "has_promotion": doc.metadata.get("has_promotion"),
                "discount_percent": doc.metadata.get("discount_percent"),
                "product_url": doc.metadata.get("product_url"),
                "image_url": doc.metadata.get("image_url"),
            }
            products.append(product)

        return products

    def retrieve_by_concern(
        self,
        skin_concerns: List[str],
        skin_type: Optional[str] = None,
        brand: Optional[str] = None,
        top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products by skin concerns

        Args:
            skin_concerns: List of skin concerns (e.g., ["hydration", "wrinkles"])
            skin_type: Optional skin type filter
            brand: Optional brand filter
            top_k: Number of results

        Returns:
            List of matching products
        """
        # Build query
        query_parts = [f"skin concerns: {', '.join(skin_concerns)}"]
        if skin_type:
            query_parts.append(f"suitable for {skin_type} skin")

        query = " | ".join(query_parts)

        # Build filter
        filter_dict = None
        if brand:
            filter_dict = {"brand": brand}

        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter_dict=filter_dict
        )

        return self._format_results(results)

    def retrieve_by_category(
        self,
        category: str,
        brand: Optional[str] = None,
        max_price_krw: Optional[int] = None,
        top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products by category

        Args:
            category: Product category (e.g., "Serum", "Cream")
            brand: Optional brand filter
            max_price_krw: Optional maximum price
            top_k: Number of results

        Returns:
            List of matching products
        """
        query = f"category: {category}"

        filter_dict = {}
        if brand:
            filter_dict["brand"] = brand
        if max_price_krw:
            filter_dict["price_krw"] = {"$lte": max_price_krw}

        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter_dict=filter_dict if filter_dict else None
        )

        return self._format_results(results)

    def retrieve_promotions(
        self,
        brand: Optional[str] = None,
        top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products currently on promotion

        Args:
            brand: Optional brand filter
            top_k: Number of results

        Returns:
            List of products with active promotions
        """
        query = "promotion discount sale special offer"

        filter_dict = {"has_promotion": True}
        if brand:
            filter_dict["brand"] = brand

        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter_dict=filter_dict
        )

        return self._format_results(results)

    def retrieve_by_keywords(
        self,
        keywords: str,
        brand: Optional[str] = None,
        top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Free-text search for products

        Args:
            keywords: Search keywords
            brand: Optional brand filter
            top_k: Number of results

        Returns:
            List of matching products
        """
        filter_dict = None
        if brand:
            filter_dict = {"brand": brand}

        results = self.vector_store.similarity_search_with_score(
            query=keywords,
            k=top_k,
            filter_dict=filter_dict
        )

        return self._format_results(results)

    def _format_results(self, results: List[tuple]) -> List[Dict[str, Any]]:
        """Format search results into product dictionaries"""
        products = []
        for doc, score in results:
            product = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(1 - score),
                "product_id": doc.metadata.get("product_id"),
                "name": doc.metadata.get("name"),
                "brand": doc.metadata.get("brand"),
                "brand_kr": doc.metadata.get("brand_kr"),
                "category": doc.metadata.get("category"),
                "price_krw": doc.metadata.get("price_krw"),
                "has_promotion": doc.metadata.get("has_promotion"),
                "discount_percent": doc.metadata.get("discount_percent"),
                "product_url": doc.metadata.get("product_url"),
                "image_url": doc.metadata.get("image_url"),
            }
            products.append(product)
        return products

    def get_product_context_for_llm(
        self,
        products: List[Dict[str, Any]],
        max_products: int = 3
    ) -> str:
        """
        Format retrieved products as context for LLM message generation

        Args:
            products: List of retrieved products
            max_products: Maximum products to include

        Returns:
            Formatted string for LLM context
        """
        context_parts = []

        for i, product in enumerate(products[:max_products], 1):
            parts = [
                f"[Product {i}]",
                f"Name: {product['name']}",
                f"Brand: {product['brand']} ({product.get('brand_kr', '')})",
                f"Category: {product.get('category', 'N/A')}",
                f"Price: {product.get('price_krw', 0):,}원",
            ]

            if product.get('has_promotion'):
                parts.append(f"Promotion: {product.get('discount_percent', 0)}% OFF")

            # Add relevant content snippet
            content = product.get('content', '')
            if content:
                # Extract description part
                if 'Description:' in content:
                    desc_start = content.find('Description:') + len('Description:')
                    desc_end = content.find('\n', desc_start)
                    if desc_end == -1:
                        desc_end = min(desc_start + 200, len(content))
                    description = content[desc_start:desc_end].strip()
                    if len(description) > 200:
                        description = description[:200] + "..."
                    parts.append(f"Description: {description}")

            parts.append(f"URL: {product.get('product_url', 'N/A')}")
            context_parts.append("\n".join(parts))

        return "\n\n".join(context_parts)


# Test function
def test_retriever():
    """Test the retriever with a sample persona"""
    # Sample persona
    test_persona = {
        "name": "Test User",
        "skin_type": "Dry",
        "skin_concerns": ["Hydration", "Anti-aging"],
        "preferred_brands": ["LANEIGE", "Sulwhasoo"],
        "shopping_pattern": {
            "avg_purchase": "50000-80000원"
        },
        "purchase_triggers": ["moisturizing", "premium quality"],
        "lifestyle": "Busy professional seeking effective skincare"
    }

    print("Testing ProductRetriever...")
    retriever = ProductRetriever()

    print("\n1. Testing persona-based retrieval:")
    products = retriever.retrieve_for_persona(test_persona, top_k=3)
    for p in products:
        print(f"  - {p['name']} ({p['brand']}) - Score: {p['relevance_score']:.3f}")

    print("\n2. Testing concern-based retrieval:")
    products = retriever.retrieve_by_concern(
        skin_concerns=["hydration", "brightening"],
        skin_type="Dry",
        top_k=3
    )
    for p in products:
        print(f"  - {p['name']} ({p['brand']})")

    print("\n3. Testing keyword search:")
    products = retriever.retrieve_by_keywords("vitamin C serum brightening", top_k=3)
    for p in products:
        print(f"  - {p['name']} ({p['brand']})")

    print("\n4. Getting LLM context:")
    context = retriever.get_product_context_for_llm(products)
    print(context[:500] + "..." if len(context) > 500 else context)


if __name__ == "__main__":
    test_retriever()
