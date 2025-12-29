import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class SegmentPrototype:
    """세그먼트 프로토타입"""
    id: str
    name_ko: str
    name_en: str
    description: str
    sample_reviews: List[str]   

 
SEGMENT_PROTOTYPES = [
    SegmentPrototype(
        id="conscious_consumer",
        name_ko="의식 있는 소비자",
        name_en="Conscious Consumer",
        description="환경, 윤리적 소싱, 사회적 책임 중시",
        sample_reviews=[
            "천연 성분이라 안심하고 사용해요. 동물실험 안 해서 좋고요.",
            "리필 용기가 있어서 환경에도 좋고 가격도 절약돼요.",
            "비건 제품이라 믿고 씁니다. 성분도 깨끗하고요.",
            "자연유래 성분 95%라 피부에 자극이 없어요.",
            "친환경 패키징이라 분리수거 할 때 마음이 편해요."
        ]
    ),
    SegmentPrototype(
        id="high_end_hauler",
        name_ko="하이엔드 수집가",
        name_en="High-End Hauler",
        description="럭셔리, 독점성, 브랜드 명성 중시",
        sample_reviews=[
            "역시 설화수, 패키징부터 고급스럽고 향도 은은해요.",
            "비싸지만 그만한 가치가 있어요. 확실히 다르더라고요.",
            "선물용으로 샀는데 포장이 너무 예쁘고 고급져요.",
            "럭셔리 라인이라 그런지 발림성이 확 다르네요.",
            "프리미엄 제품답게 효과가 확실해요. 피부결이 달라졌어요."
        ]
    ),
    SegmentPrototype(
        id="skinminimalist",
        name_ko="스킨미니멀리스트",
        name_en="Skinminimalist",
        description="간단한 루틴, 다기능 제품 선호",
        sample_reviews=[
            "이거 하나로 끝! 세럼+크림 역할 다 해서 편해요.",
            "스킨케어 귀찮아하는데 올인원이라 딱이에요.",
            "복잡한 거 싫어서 이것만 써요. 간단하게 끝.",
            "아침에 바빠서 멀티 제품만 찾는데 이게 최고예요.",
            "스텝 줄이고 싶어서 샀는데 보습도 되고 좋아요."
        ]
    ),
    SegmentPrototype(
        id="diy_diva",
        name_ko="DIY 디바",
        name_en="DIY Diva",
        description="직접 만들고 커스터마이징 즐김",
        sample_reviews=[
            "다른 오일이랑 섞어서 쓰니까 더 좋아요.",
            "나만의 레시피로 마스크팩 만들어 써요.",
            "여러 제품 조합해서 커스텀해서 쓰는 중이에요.",
            "앰플 몇 방울 섞어서 쓰면 효과 두 배!",
            "이거 파운데이션이랑 믹스하면 글로우가 예술이에요."
        ]
    ),
    SegmentPrototype(
        id="wellness_warrior",
        name_ko="웰니스 전사",
        name_en="Wellness Warrior",
        description="마음챙김, 힐링, 홀리스틱 뷰티 추구",
        sample_reviews=[
            "향이 너무 좋아서 바르면서 힐링돼요.",
            "마사지하면서 바르니까 스트레스가 풀려요.",
            "아로마 향이 편안해서 자기 전에 꼭 발라요.",
            "피부 케어하면서 마음까지 치유되는 느낌이에요.",
            "명상하는 기분으로 천천히 발라요. 나만의 시간."
        ]
    ),
    SegmentPrototype(
        id="savvy_shopper",
        name_ko="현명한 쇼퍼",
        name_en="Savvy Shopper",
        description="가성비 중시, 합리적 소비",
        sample_reviews=[
            "가성비 최고! 이 가격에 이 품질이면 대만족이에요.",
            "세일할 때 샀는데 진짜 잘 산 것 같아요.",
            "용량 대비 가격이 너무 착해요. 재구매 확정.",
            "비싼 거 안 부러워요. 이거면 충분해요.",
            "할인 쿠폰 써서 반값에 샀어요. 효과는 똑같아요."
        ]
    ),
    SegmentPrototype(
        id="beautopian",
        name_ko="뷰토피안",
        name_en="Beautopian",
        description="트렌드 민감, SNS 활발, 즉각적 효과 선호",
        sample_reviews=[
            "유튜브에서 보고 샀는데 진짜 좋아요! 추천템 맞음.",
            "요즘 핫한 제품이라 써봤는데 역시 인기 있는 이유가 있네요.",
            "바르자마자 광나요! 셀카 찍으면 뽀샤시해요.",
            "틱톡에서 난리났던 그 제품! 직접 써보니 진짜 대박.",
            "인스타에서 예쁘게 나와서 샀는데 실물도 예뻐요."
        ]
    ),
    SegmentPrototype(
        id="non_conformist",
        name_ko="비순응적 혁명가",
        name_en="Non-Conformist Revolutionary",
        description="개성 추구, 고정관념 타파",
        sample_reviews=[
            "남자인데 써도 전혀 어색하지 않아요. 피부는 성별 없죠.",
            "독특한 컬러라서 샀어요. 남들 다 쓰는 건 재미없잖아요.",
            "나만의 스타일로 연출하기 좋아요. 개성 표현 가능.",
            "젠더리스 콘셉트라 누구나 쓸 수 있어서 좋아요.",
            "평범한 건 싫어서 이런 특이한 제품 찾았어요."
        ]
    )
]


class ReviewSegmenter:
 

    def __init__(self):
        self.segment_embeddings = {} 
        self.model = "text-embedding-3-small"

    def get_embedding(self, text: str) -> List[float]:
 
        response = client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
 
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # 빈 텍스트 처리
            batch = [t if t.strip() else "리뷰 없음" for t in batch]

            response = client.embeddings.create(
                model=self.model,
                input=batch
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

            if (i + batch_size) % 1000 == 0:
                print(f"  임베딩 진행: {min(i + batch_size, len(texts))}/{len(texts)}")

        return all_embeddings

    def build_segment_embeddings(self):
 

        for prototype in SEGMENT_PROTOTYPES:
 
            combined_text = " ".join(prototype.sample_reviews)

 
            embeddings = []
            for review in prototype.sample_reviews:
                emb = self.get_embedding(review)
                embeddings.append(emb)

 
            avg_embedding = np.mean(embeddings, axis=0).tolist()
            self.segment_embeddings[prototype.id] = {
                "embedding": avg_embedding,
                "prototype": prototype
            }
 

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
 
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def classify_review(self, review_embedding: List[float]) -> Tuple[str, float, Dict[str, float]]:
 
        similarities = {}

        for segment_id, data in self.segment_embeddings.items():
            sim = self.cosine_similarity(review_embedding, data["embedding"])
            similarities[segment_id] = sim

 
        best_segment = max(similarities, key=similarities.get)
        best_score = similarities[best_segment]

        return best_segment, best_score, similarities

    def load_reviews(self, reviews_path: str) -> List[Dict]:
 
 

        with open(reviews_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        reviews = data.get("reviews", [])
 
        return reviews

    def segment_all_reviews(self, reviews: List[Dict]) -> List[Dict]:
 
        review_texts = [r.get("review_text", "") for r in reviews]
 
        embeddings = self.get_embeddings_batch(review_texts)

        # 분류
        print("  세그먼트 분류 중   ")
        results = []

        for i, (review, embedding) in enumerate(zip(reviews, embeddings)):
            segment_id, score, all_scores = self.classify_review(embedding)

            result = {
                **review,
                "segment_id": segment_id,
                "segment_score": round(score, 4),
                "all_segment_scores": {k: round(v, 4) for k, v in all_scores.items()}
            }
            results.append(result)

            if (i + 1) % 1000 == 0:
                print(f"  분류 진행: {i + 1}/{len(reviews)}")

        return results

    def analyze_segments(self, segmented_reviews: List[Dict]) -> Dict:
 
        analysis = {}

        for prototype in SEGMENT_PROTOTYPES:
            segment_id = prototype.id
            segment_reviews = [r for r in segmented_reviews if r["segment_id"] == segment_id]

            if not segment_reviews:
                continue

            # 기본 통계
            avg_rating = np.mean([r.get("rating", 0) for r in segment_reviews])
            avg_score = np.mean([r.get("segment_score", 0) for r in segment_reviews])
 
            age_dist = Counter([r.get("age_group", "미상") for r in segment_reviews])
 
            skin_dist = Counter([r.get("skin_type", "미상") for r in segment_reviews])
 
            top_reviews = sorted(segment_reviews, key=lambda x: x.get("segment_score", 0), reverse=True)[:10]

            analysis[segment_id] = {
                "name_ko": prototype.name_ko,
                "name_en": prototype.name_en,
                "description": prototype.description,
                "count": len(segment_reviews),
                "percentage": round(len(segment_reviews) / len(segmented_reviews) * 100, 1),
                "avg_rating": round(avg_rating, 2),
                "avg_similarity_score": round(avg_score, 4),
                "age_distribution": dict(age_dist.most_common(5)),
                "skin_type_distribution": dict(skin_dist.most_common(5)),
                "top_reviews": [
                    {
                        "text": r.get("review_text", "")[:200],
                        "rating": r.get("rating", 0),
                        "score": r.get("segment_score", 0),
                        "product": r.get("product_name", "")[:50]
                    }
                    for r in top_reviews
                ]
            }

            print(f"  - {prototype.name_ko}: {len(segment_reviews)}개 ({analysis[segment_id]['percentage']}%)")

        return analysis

    def save_results(self, segmented_reviews: List[Dict], analysis: Dict, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with open(output_path / "segmented_reviews.json", "w", encoding="utf-8") as f:
            json.dump({
                "total_count": len(segmented_reviews),
                "reviews": segmented_reviews
            }, f, ensure_ascii=False, indent=2)

        with open(output_path / "segment_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)


        for prototype in SEGMENT_PROTOTYPES:
            segment_reviews = [r for r in segmented_reviews if r["segment_id"] == prototype.id]
            with open(output_path / f"segment_{prototype.id}.json", "w", encoding="utf-8") as f:
                json.dump({
                    "segment": prototype.id,
                    "name_ko": prototype.name_ko,
                    "count": len(segment_reviews),
                    "reviews": segment_reviews
                }, f, ensure_ascii=False, indent=2)

    def run(self, reviews_path: str, output_dir: str):
        self.build_segment_embeddings()

        reviews = self.load_reviews(reviews_path)

        segmented_reviews = self.segment_all_reviews(reviews)

        analysis = self.analyze_segments(segmented_reviews)

        self.save_results(segmented_reviews, analysis, output_dir)

        return segmented_reviews, analysis


def main():
    segmenter = ReviewSegmenter()
 
    reviews_path = ""
    output_dir = ""

    segmented_reviews, analysis = segmenter.run(reviews_path, output_dir)
 
    print("\n[세그먼트 분포]")
    for seg_id, info in sorted(analysis.items(), key=lambda x: x[1]["count"], reverse=True):
 

if __name__ == "__main__":
    main()
