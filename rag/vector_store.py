"""
Vector Store Module for Product RAG
Uses ChromaDB for vector storage and retrieval
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    PROCESSED_PRODUCTS_PATH,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    get_openai_api_key,
)

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print(f"Missing required packages. Install with:")
    print("pip install langchain-openai langchain-chroma langchain-core langchain-text-splitters chromadb")
    raise e


class ProductVectorStore:
    """Vector store for product data using ChromaDB"""

    def __init__(
        self,
        persist_directory: Path = CHROMA_PERSIST_DIR,
        collection_name: str = "amore_products"
    ):
        self.persist_directory = str(persist_directory)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=get_openai_api_key()  # Fetch at runtime for Streamlit Cloud
        )
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )

    def _create_document_content(self, product: Dict) -> str:
        """Create searchable text content from product data"""
        parts = []

        # Product name and brand
        parts.append(f"Product: {product['name']}")
        parts.append(f"Brand: {product['brand']} ({product.get('brand_kr', product['brand'])})")

        # Category
        if product.get('category'):
            parts.append(f"Category: {product['category']}")

        # Price info
        if product.get('price_krw'):
            price_str = f"Price: {product['price_krw']:,}원"
            if product.get('has_promotion') and product.get('discount_percent'):
                price_str += f" ({product['discount_percent']}% OFF)"
            parts.append(price_str)

        # Skin types
        if product.get('skin_types'):
            parts.append(f"Suitable for: {', '.join(product['skin_types'])}")

        # Skin concerns
        if product.get('skin_concerns'):
            parts.append(f"Addresses: {', '.join(product['skin_concerns'])}")

        # Benefits
        if product.get('benefits'):
            parts.append(f"Benefits: {', '.join(product['benefits'])}")

        # Description
        if product.get('description'):
            parts.append(f"Description: {product['description']}")

        # Ingredients (if available)
        if product.get('ingredients'):
            # Truncate very long ingredient lists
            ingredients = product['ingredients']
            if len(ingredients) > 500:
                ingredients = ingredients[:500] + "..."
            parts.append(f"Key Ingredients: {ingredients}")

        return "\n".join(parts)

    def _create_metadata(self, product: Dict) -> Dict[str, Any]:
        """Create metadata for filtering"""
        return {
            "product_id": product.get("product_id", ""),
            "name": product.get("name", ""),
            "brand": product.get("brand", ""),
            "brand_kr": product.get("brand_kr", ""),
            "category": product.get("category", ""),
            "price_krw": product.get("price_krw", 0),
            "has_promotion": product.get("has_promotion", False),
            "discount_percent": product.get("discount_percent", 0),
            "product_url": product.get("product_url", ""),
            "image_url": product.get("image_url", ""),
            # Store as comma-separated strings for Chroma compatibility
            "skin_types": ",".join(product.get("skin_types", [])),
            "skin_concerns": ",".join(product.get("skin_concerns", [])),
            "benefits": ",".join(product.get("benefits", [])),
        }

    def load_processed_products(
        self,
        filepath: Path = PROCESSED_PRODUCTS_PATH
    ) -> List[Dict]:
        """Load processed product data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("products", [])

    def create_documents(self, products: List[Dict]) -> List[Document]:
        """Convert products to LangChain Documents"""
        documents = []

        for product in products:
            content = self._create_document_content(product)
            metadata = self._create_metadata(product)

            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)

        return documents

    def build_vector_store(
        self,
        products: Optional[List[Dict]] = None,
        force_rebuild: bool = False
    ) -> Chroma:
        """Build or load the vector store"""
        persist_path = Path(self.persist_directory)

        # Check if vector store already exists
        if persist_path.exists() and not force_rebuild:
            print(f"Loading existing vector store from {self.persist_directory}...")
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Loaded vector store with {self.vector_store._collection.count()} documents")
            return self.vector_store

        # Load products if not provided
        if products is None:
            print("Loading processed products...")
            products = self.load_processed_products()

        print(f"Creating documents from {len(products)} products...")
        documents = self.create_documents(products)

        # Split documents if needed (for very long descriptions)
        print("Splitting documents...")
        split_docs = []
        for doc in documents:
            if len(doc.page_content) > CHUNK_SIZE:
                splits = self.text_splitter.split_documents([doc])
                # Keep metadata for all splits
                for split in splits:
                    split.metadata = doc.metadata
                split_docs.extend(splits)
            else:
                split_docs.append(doc)

        print(f"Total documents after splitting: {len(split_docs)}")

        # Create vector store
        print("Building vector store (this may take a few minutes)...")
        persist_path.mkdir(parents=True, exist_ok=True)

        self.vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory
        )

        print(f"Vector store built with {self.vector_store._collection.count()} documents")
        return self.vector_store

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """Search for similar products"""
        if self.vector_store is None:
            self.build_vector_store()

        if filter_dict:
            results = self.vector_store.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vector_store.similarity_search(query, k=k)

        return results

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[tuple]:
        """Search with relevance scores"""
        if self.vector_store is None:
            self.build_vector_store()

        if filter_dict:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vector_store.similarity_search_with_score(query, k=k)

        return results

    def get_retriever(self, search_kwargs: Optional[Dict] = None):
        """Get a retriever for use with LangChain"""
        if self.vector_store is None:
            self.build_vector_store()

        kwargs = search_kwargs or {"k": 5}
        return self.vector_store.as_retriever(search_kwargs=kwargs)


def build_vector_store_from_scratch():
    """Build the vector store from preprocessed data"""
    from preprocess import run_preprocessing

    # First preprocess the data
    print("Step 1: Preprocessing raw product data...")
    products = run_preprocessing()

    # Then build vector store
    print("\nStep 2: Building vector store...")
    vs = ProductVectorStore()
    vs.build_vector_store(products, force_rebuild=True)

    print("\nVector store build complete!")
    return vs


if __name__ == "__main__":
    build_vector_store_from_scratch()
