#!/usr/bin/env python3
"""
Build script for RAG system
Runs preprocessing and builds vector store
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("="*60)
    print("RAG SYSTEM BUILD SCRIPT")
    print("="*60)

    # Step 1: Preprocess data
    print("\n[STEP 1/2] Preprocessing product data...")
    print("-"*60)

    from preprocess import run_preprocessing
    products = run_preprocessing()

    if not products:
        print("ERROR: No products after preprocessing!")
        return False

    # Step 2: Build vector store
    print("\n[STEP 2/2] Building vector store...")
    print("-"*60)

    from vector_store import ProductVectorStore
    vs = ProductVectorStore()
    vs.build_vector_store(products, force_rebuild=True)

    # Verify
    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)

    # Quick test
    print("\nRunning quick verification test...")
    results = vs.similarity_search("moisturizing cream for dry skin", k=3)
    print(f"Test search returned {len(results)} results")

    if results:
        print("\nSample result:")
        print(f"  Product: {results[0].metadata.get('name', 'N/A')}")
        print(f"  Brand: {results[0].metadata.get('brand', 'N/A')}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
