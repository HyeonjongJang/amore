"""
Data Preprocessing Module for RAG System
Cleans and prepares product data for vector embedding
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    RAW_PRODUCTS_PATH,
    PROCESSED_PRODUCTS_PATH,
    EXCLUDE_BRANDS,
    COSMETIC_BRANDS,
    MIN_DESCRIPTION_LENGTH,
    BRAND_NAME_MAPPING,
)


class ProductPreprocessor:
    """Preprocesses raw product data for RAG system"""

    def __init__(self):
        self.stats = {
            "total_raw": 0,
            "excluded_brand": 0,
            "empty_description": 0,
            "short_description": 0,
            "unknown_brand_kept": 0,
            "final_count": 0,
            "with_ingredients": 0,
        }

    def load_raw_data(self, filepath: Path = RAW_PRODUCTS_PATH) -> Dict:
        """Load raw product JSON data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.stats["total_raw"] = len(data.get("products", []))
        return data

    def clean_description(self, description: str) -> str:
        """Clean and normalize product description"""
        if not description:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', description)

        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)

        # Remove special unicode characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s.,!?;:\-\'\"()/&%#@+*=]', '', text)

        # Trim
        text = text.strip()

        return text

    def extract_benefits_from_description(self, description: str) -> List[str]:
        """Extract key benefits from description text"""
        benefits = []

        # Common benefit keywords
        benefit_patterns = [
            r'(moisturiz\w+)',
            r'(hydrat\w+)',
            r'(brighten\w+)',
            r'(anti-aging)',
            r'(wrinkle\w*)',
            r'(firm\w+)',
            r'(sooth\w+)',
            r'(calm\w+)',
            r'(repair\w+)',
            r'(protect\w+)',
            r'(nourish\w+)',
            r'(revitaliz\w+)',
            r'(refresh\w+)',
            r'(glow\w*)',
            r'(radian\w+)',
        ]

        desc_lower = description.lower()
        for pattern in benefit_patterns:
            matches = re.findall(pattern, desc_lower)
            benefits.extend(matches)

        return list(set(benefits))

    def normalize_skin_concerns(self, tags: List[str], skin_concerns: List[str]) -> List[str]:
        """Normalize and extract skin concerns from tags and existing concerns"""
        concerns = set(skin_concerns) if skin_concerns else set()

        # Mapping of tag keywords to standardized concerns
        concern_mapping = {
            "DRYNESS": "Dryness/Hydration",
            "HYDRATION": "Dryness/Hydration",
            "ANTI-AGING": "Anti-aging/Wrinkles",
            "WRINKLES": "Anti-aging/Wrinkles",
            "BRIGHTENING": "Dullness/Brightening",
            "DULLNESS": "Dullness/Brightening",
            "SENSITIVE": "Redness/Sensitive",
            "REDNESS": "Redness/Sensitive",
            "ACNE": "Acne/Blemish",
            "BLEMISH": "Acne/Blemish",
            "PORE": "Pores/Oiliness",
            "OILY": "Pores/Oiliness",
            "FIRMNESS": "Firmness/Elasticity",
            "ELASTICITY": "Firmness/Elasticity",
        }

        for tag in tags:
            tag_upper = tag.upper()
            for keyword, concern in concern_mapping.items():
                if keyword in tag_upper:
                    concerns.add(concern)

        return list(concerns)

    def normalize_skin_types(self, tags: List[str], skin_types: List[str]) -> List[str]:
        """Normalize skin types"""
        types = set(skin_types) if skin_types else set()

        type_keywords = {
            "DRY": "Dry",
            "OILY": "Oily",
            "COMBINATION": "Combination",
            "SENSITIVE": "Sensitive",
            "NORMAL": "Normal",
            "ALL SKIN": "All Skin Types",
        }

        for tag in tags:
            tag_upper = tag.upper()
            for keyword, skin_type in type_keywords.items():
                if keyword in tag_upper:
                    types.add(skin_type)

        return list(types)

    def extract_category(self, tags: List[str], name: str) -> str:
        """Extract product category from tags and name"""
        category_keywords = {
            "CREAM": "Cream",
            "SERUM": "Serum",
            "ESSENCE": "Essence",
            "TONER": "Toner",
            "CLEANSER": "Cleanser",
            "MOISTURIZER": "Moisturizer",
            "MASK": "Mask",
            "SUNSCREEN": "Sunscreen",
            "SPF": "Sunscreen",
            "FOUNDATION": "Foundation",
            "LIPSTICK": "Lipstick",
            "LIP": "Lip Product",
            "EYE": "Eye Product",
            "MASCARA": "Mascara",
            "POWDER": "Powder",
            "CUSHION": "Cushion",
            "AMPOULE": "Ampoule",
            "OIL": "Oil",
            "MIST": "Mist",
            "LOTION": "Lotion",
            "EMULSION": "Emulsion",
            "SHAMPOO": "Shampoo",
            "CONDITIONER": "Conditioner",
            "BODY": "Body Care",
            "HAND": "Hand Care",
        }

        # Check tags first
        for tag in tags:
            tag_upper = tag.upper()
            for keyword, category in category_keywords.items():
                if keyword in tag_upper:
                    return category

        # Check product name
        name_upper = name.upper()
        for keyword, category in category_keywords.items():
            if keyword in name_upper:
                return category

        return "Other"

    def should_include_product(self, product: Dict) -> bool:
        """Determine if product should be included in RAG"""
        brand = product.get("brand", "Unknown")
        description = product.get("description", "")

        # Exclude specific brands
        if brand in EXCLUDE_BRANDS:
            self.stats["excluded_brand"] += 1
            return False

        # Check description
        if not description:
            self.stats["empty_description"] += 1
            return False

        cleaned_desc = self.clean_description(description)
        if len(cleaned_desc) < MIN_DESCRIPTION_LENGTH:
            self.stats["short_description"] += 1
            return False

        # Keep Unknown brand if it has good description
        if brand == "Unknown":
            self.stats["unknown_brand_kept"] += 1

        return True

    def process_product(self, product: Dict) -> Optional[Dict]:
        """Process a single product for RAG"""
        if not self.should_include_product(product):
            return None

        # Clean description
        description = self.clean_description(product.get("description", ""))
        ingredients = product.get("ingredients", "")

        # Get normalized data
        tags = product.get("tags", [])
        skin_concerns = self.normalize_skin_concerns(
            tags, product.get("skin_concerns", [])
        )
        skin_types = self.normalize_skin_types(
            tags, product.get("skin_types", [])
        )
        category = self.extract_category(tags, product.get("name", ""))
        benefits = self.extract_benefits_from_description(description)

        # Get brand info
        brand = product.get("brand", "Unknown")
        brand_kr = BRAND_NAME_MAPPING.get(brand, brand)

        # Calculate price in KRW (approximate)
        price_usd = product.get("price", 0)
        price_krw = int(price_usd * 1350) if price_usd else 0

        compare_price_usd = product.get("compare_at_price", 0)
        compare_price_krw = int(compare_price_usd * 1350) if compare_price_usd else 0

        # Check for promotion
        has_promotion = compare_price_krw > price_krw
        discount_percent = 0
        if has_promotion and compare_price_krw > 0:
            discount_percent = int((1 - price_krw / compare_price_krw) * 100)

        processed = {
            "product_id": product.get("product_id", ""),
            "name": product.get("name", ""),
            "brand": brand,
            "brand_kr": brand_kr,
            "category": category,
            "price_usd": price_usd,
            "price_krw": price_krw,
            "compare_price_krw": compare_price_krw,
            "has_promotion": has_promotion,
            "discount_percent": discount_percent,
            "description": description,
            "ingredients": ingredients,
            "skin_types": skin_types,
            "skin_concerns": skin_concerns,
            "benefits": benefits,
            "tags": tags,
            "product_url": product.get("product_url", ""),
            "image_url": product.get("image_urls", [""])[0] if product.get("image_urls") else "",
        }

        if ingredients:
            self.stats["with_ingredients"] += 1

        return processed

    def process_all(self, raw_data: Dict) -> List[Dict]:
        """Process all products"""
        products = raw_data.get("products", [])
        processed_products = []

        for product in products:
            processed = self.process_product(product)
            if processed:
                processed_products.append(processed)

        self.stats["final_count"] = len(processed_products)
        return processed_products

    def save_processed_data(
        self,
        products: List[Dict],
        filepath: Path = PROCESSED_PRODUCTS_PATH
    ):
        """Save processed products to JSON"""
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        output = {
            "stats": self.stats,
            "products": products
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(products)} products to {filepath}")

    def print_stats(self):
        """Print preprocessing statistics"""
        print("\n" + "="*50)
        print("PREPROCESSING STATISTICS")
        print("="*50)
        print(f"Total raw products:      {self.stats['total_raw']:,}")
        print(f"Excluded (brand):        {self.stats['excluded_brand']:,}")
        print(f"Excluded (no desc):      {self.stats['empty_description']:,}")
        print(f"Excluded (short desc):   {self.stats['short_description']:,}")
        print(f"Unknown brand kept:      {self.stats['unknown_brand_kept']:,}")
        print(f"With ingredients:        {self.stats['with_ingredients']:,}")
        print("-"*50)
        print(f"FINAL COUNT:             {self.stats['final_count']:,}")
        print("="*50 + "\n")


def run_preprocessing():
    """Run the full preprocessing pipeline"""
    print("Starting product data preprocessing...")

    preprocessor = ProductPreprocessor()

    # Load raw data
    print(f"Loading raw data from {RAW_PRODUCTS_PATH}...")
    raw_data = preprocessor.load_raw_data()

    # Process all products
    print("Processing products...")
    processed_products = preprocessor.process_all(raw_data)

    # Save results
    preprocessor.save_processed_data(processed_products)

    # Print statistics
    preprocessor.print_stats()

    return processed_products


if __name__ == "__main__":
    run_preprocessing()
