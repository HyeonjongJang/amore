# CRM Message Generation System

아모레퍼시픽 AI Innovation Challenge - Multi-Agent CRM 메시지 자동 생성 시스템

---

## 1. Overview

이 시스템은 고객 페르소나 분석을 기반으로 개인화된 CRM 마케팅 메시지를 자동 생성하는 **Multi-Agent AI 솔루션**입니다. LangGraph를 활용한 워크플로우와 RAG(Retrieval-Augmented Generation)를 통해 브랜드 톤앤매너에 맞는 고품질 메시지를 생성합니다.

### 1.1 핵심 요구사항
- ✅ 다양한 고객 페르소나 기반 상품 추천 메시지
- ✅ 브랜드별 톤(Tone) 자동 조정
- ✅ 기계적이지 않은 감성적 자연어 생성
- ✅ RAG 등 AI 기술 적용 (단순 프롬프팅 X)
- ✅ 메시지 형식: 제목 40자 이내, 내용 350자 이내

### 1.2 차별화 포인트
| 포인트 | 설명 |
|--------|------|
| Multi-Agent 아키텍처 | 4개의 전문 AI Agent가 협업하여 메시지 생성 |
| RAG 시스템 | ChromaDB 기반 제품 검색 및 추천 |
| A/B 테스트 메시지 | 메인 메시지 + 2개 대안 메시지 자동 생성 |
| 성과 예측 스코어 | 예상 CTR/CVR 자동 산출 |
| 품질 자동 검증 | 글자수, 브랜드톤, 페르소나 적합도 검증 |

---

## 2. System Architecture

### 2.1 전체 아키텍처
<img width="1006" height="854" alt="image" src="https://github.com/user-attachments/assets/f52c2a20-6b3f-4ce2-9b5c-af139fa89a33" />

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CRM Message Generation System                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐  │
│  │   INPUT     │     │              MULTI-AGENT SYSTEM                 │  │
│  │             │     │  ┌─────────────────────────────────────────┐   │  │
│  │ • 페르소나   │────▶│  │  Agent 1: Persona Analyzer              │   │  │
│  │ • 캠페인목적 │     │  │  - 페르소나 특성 분석                     │   │  │
│  │ • 브랜드    │     │  │  - 구매 동기 추출                         │   │  │
│  │ • 시즌/이벤트│     │  └──────────────┬──────────────────────────┘   │  │
│  └─────────────┘     │                 ▼                              │  │
│                      │  ┌─────────────────────────────────────────┐   │  │
│  ┌─────────────┐     │  │  Agent 2: Product Matcher (RAG)         │   │  │
│  │  RAG System │     │  │  - 페르소나 맞춤 제품 검색                │   │  │
│  │             │◀───▶│  │  - 제품 특장점 추출                      │   │  │
│  │ • Product DB│     │  │  - 가격/프로모션 정보 매칭                │   │  │
│  │ • Brand Tone│     │  └──────────────┬──────────────────────────┘   │  │
│  │ • CRM 예시  │     │                 ▼                              │  │
│  └─────────────┘     │  ┌─────────────────────────────────────────┐   │  │
│                      │  │  Agent 3: Message Generator             │   │  │
│                      │  │  - 브랜드 톤앤매너 적용                   │   │  │
│                      │  │  - 감성적 카피 생성                       │   │  │
│                      │  │  - 글자수 제한 준수                       │   │  │
│                      │  └──────────────┬──────────────────────────┘   │  │
│                      │                 ▼                              │  │
│                      │  ┌─────────────────────────────────────────┐   │  │
│                      │  │  Agent 4: Quality Checker               │   │  │
│                      │  │  - 글자수 검증                           │   │  │
│                      │  │  - 브랜드 가이드라인 준수 확인            │   │  │
│                      │  │  - 성과 예측 스코어 산출                  │   │  │
│                      │  └──────────────┬──────────────────────────┘   │  │
│                      └─────────────────┼───────────────────────────────┘  │
│                                        ▼                                  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                           OUTPUT                                    │  │
│  │  • 메인 메시지 (제목 40자 + 본문 350자)                              │  │
│  │  • A/B 테스트용 대안 메시지 2개                                      │  │
│  │  • 예상 클릭률/전환율 스코어                                         │  │
│  │  • 추천 발송 시간대                                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 LangGraph 워크플로우

```
┌──────────────────┐
│   Entry Point    │
│  (Initial State) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ analyze_persona  │ ──→ PersonaAnalyzerAgent
│                  │     • 페르소나 특성 분석
│                  │     • 구매 동기/감성 트리거 추출
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  match_products  │ ──→ ProductMatcherAgent + RAG
│                  │     • 벡터DB에서 제품 검색
│                  │     • LLM으로 최적 제품 선정
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│generate_messages │ ──→ MessageGeneratorAgent
│                  │     • 브랜드 톤앤매너 적용
│                  │     • 메인 + 대안 메시지 생성
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  check_quality   │ ──→ QualityCheckerAgent
│                  │     • 글자수/톤 검증
│                  │     • 성과 예측 스코어 산출
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  prepare_output  │ ──→ 최종 결과 조합
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│       END        │
└──────────────────┘
```

---

## 3. Implementation Methodology

### 3.1 Multi-Agent 설계 원칙

각 Agent는 **단일 책임 원칙(SRP)**에 따라 설계되었습니다:

| Agent | 역할 | 입력 | 출력 |
|-------|------|------|------|
| **PersonaAnalyzerAgent** | 고객 분석 | 페르소나 정보, 캠페인 목적 | 구매 동기, 감성 트리거, 추천 톤 |
| **ProductMatcherAgent** | 제품 추천 | 페르소나 분석 결과, 브랜드 | 추천 제품 3개, 셀링 포인트 |
| **MessageGeneratorAgent** | 메시지 생성 | 분석 결과, 제품 정보, 브랜드 톤 | 메인 메시지 + 대안 2개 |
| **QualityCheckerAgent** | 품질 검증 | 생성된 메시지, 페르소나, 브랜드 | 품질 점수, 성과 예측, 개선 제안 |

### 3.2 RAG (Retrieval-Augmented Generation) 파이프라인
<img width="1010" height="432" alt="image" src="https://github.com/user-attachments/assets/1610ad27-d2ee-4caa-a884-cb7a1dddaaeb" />

```
[Product Data] ──→ [Preprocessing] ──→ [Embedding] ──→ [ChromaDB]
     │                   │                  │              │
     │                   │                  │              │
     ▼                   ▼                  ▼              ▼
final_products.json  정규화/필터링    OpenAI           벡터 저장소
(2,753 products)     (516 products)  text-embedding   (3,096 chunks)
                                     -3-small
```

**RAG 검색 프로세스:**
1. 페르소나 피부타입/고민 + 브랜드로 검색 쿼리 생성
2. ChromaDB에서 유사도 검색 (top_k=7)
3. 중복 제거 후 LLM이 최적 3개 제품 선정
4. 제품 URL, 이미지 URL 자동 매핑

### 3.3 브랜드 톤앤매너 적용

각 브랜드별로 정의된 톤앤매너가 메시지 생성에 적용됩니다:

| 브랜드 | 톤 | 특징 |
|--------|-----|------|
| 설화수 | 고급스럽고 우아함 | 한방, 격조, 이모지 최소화 |
| 라네즈 | 세련되고 활기참 | 수분, 광채, 💧✨ 이모지 |
| 헤라 | 세련되고 당당함 | 서울 감성, 모던, 시크 |
| 이니스프리 | 자연스럽고 친근함 | 제주, 비건, 🌿🍃 이모지 |
| 아이오페 | 과학적이고 신뢰감 | 바이오, 레티놀, 전문적 |
| 에뛰드 | 발랄하고 즐거움 | 컬러풀, 💕🎀 이모지 적극 활용 |

---

## 4. Project Structure

```
agent10_crm/
├── agents/                     # Multi-Agent 모듈
│   ├── __init__.py
│   ├── persona_analyzer.py     # Agent 1: 페르소나 분석
│   ├── product_matcher.py      # Agent 2: 제품 매칭 (RAG)
│   ├── message_generator.py    # Agent 3: 메시지 생성
│   └── quality_checker.py      # Agent 4: 품질 검증
│
├── rag/                        # RAG 시스템
│   ├── __init__.py
│   ├── preprocess.py           # 제품 데이터 전처리
│   ├── vector_store.py         # ChromaDB 벡터 스토어
│   ├── retriever.py            # 제품 검색 리트리버
│   ├── build_rag.py            # RAG 빌드 스크립트
│   └── chroma_db/              # 벡터 DB 저장소
│
├── data/
│   ├── personas/               # 고객 페르소나 데이터 (7개)
│   │   └── personas.json
│   ├── brand_tones/            # 브랜드 톤앤매너 가이드 (12개)
│   │   └── brand_tones.json
│   ├── crm_examples/           # CRM 메시지 예시
│   │   └── crm_examples.json
│   └── products/               # 처리된 제품 데이터
│       └── processed_products.json
│
├── ui/
│   └── streamlit_app.py        # Streamlit 웹 UI
│
├── main.py                     # LangGraph 워크플로우 메인
├── config.py                   # 설정 파일
├── requirements.txt            # 의존성 패키지
└── README.md
```

---

## 5. Installation & Setup

### 5.1 Prerequisites
- Python 3.10+
- OpenAI API Key

### 5.2 Installation Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd agent10_crm

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

# 5. Build Vector Store (First time only)
cd rag
python vector_store.py
```

### 5.3 Dependencies

```
# Core LLM and RAG
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.20
openai>=1.10.0

# Vector database
chromadb>=0.4.22

# UI
streamlit>=1.30.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0
```

---

## 6. Usage

### 6.1 Run Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

브라우저에서 `http://localhost:8501` 접속

### 6.2 UI 사용 방법

1. **메시지 설정 (사이드바)**
   - 타겟 페르소나 선택
   - 브랜드 선택
   - 캠페인 목적 선택
   - 시즌/이벤트 선택

2. **메시지 생성**
   - "🚀 메시지 생성" 버튼 클릭

3. **결과 확인 (4개 탭)**
   - 📨 생성된 메시지: 제품별 메인/대안 메시지
   - 🛍️ 추천 제품: 제품 이미지, 상세 정보
   - 🔍 상세 분석: 페르소나 인사이트
   - 📊 품질 리포트: 점수, 예상 성과, 개선 제안

### 6.3 Run from Command Line

```python
from main import CRMMessageGenerator

generator = CRMMessageGenerator()
result = generator.generate(
    persona_id_or_name="P001",      # 페르소나 ID 또는 이름
    brand="헤라",                    # 브랜드 (한글)
    campaign_purpose="신제품 런칭",  # 캠페인 목적
    season_event="봄 신상"           # 시즌/이벤트
)

print(result)
```

---

## 7. Output Format
<img width="1040" height="493" alt="image" src="https://github.com/user-attachments/assets/d47e3f5a-c818-4ae1-9f0c-9c7e282ac481" />
<img width="1040" height="489" alt="image" src="https://github.com/user-attachments/assets/6add604a-e57f-4590-88f6-1bbeadde768d" />
<img width="1040" height="491" alt="image" src="https://github.com/user-attachments/assets/b188ba09-a5dd-410e-a9ab-916ebece46ff" />
<img width="1034" height="221" alt="image" src="https://github.com/user-attachments/assets/d13b0186-5ffd-40e0-b455-12161ea438fd" />



### 7.1 전체 응답 구조

```json
{
  "persona": {
    "id": "P001",
    "name": "트렌드세터 지영"
  },
  "brand": "헤라",
  "campaign_purpose": "신제품 런칭",
  "season_event": "봄 신상",
  "messages": {
    "product_messages": [
      {
        "product_name": "HERA Uv Protector Multi-Defense 50ml",
        "product_index": 1,
        "main_message": {
          "title": "메시지 제목 (40자 이내)",
          "body": "메시지 본문 (350자 이내)",
          "cta": "CTA 버튼 텍스트",
          "angle": "어필 각도"
        },
        "alternative_1": { ... },
        "alternative_2": { ... },
        "product_details": {
          "price_krw": 49950,
          "key_selling_points": ["..."],
          "product_url": "https://...",
          "image_url": "https://..."
        }
      }
    ],
    "overall_strategy": "전체 메시지 전략 설명"
  },
  "recommended_products": [
    {
      "product_name": "...",
      "brand": "HERA",
      "price_krw": 49950,
      "key_selling_points": ["..."],
      "persona_fit_reason": "...",
      "product_url": "...",
      "image_url": "..."
    }
  ],
  "quality_summary": {
    "scores": {
      "brand_tone": 8,
      "persona_fit": 9,
      "naturalness": 8,
      "cta_clarity": 9,
      "overall": 8
    },
    "average_score": 8.4,
    "verdict": "APPROVED",
    "char_limits_passed": true
  },
  "quality_details": {
    "predicted_performance": {
      "estimated_ctr": "2.5%",
      "estimated_cvr": "0.8%",
      "confidence": "medium"
    },
    "improvement_suggestions": ["..."],
    "strengths": ["..."],
    "recommended_send_time": "오후 6시 - 8시"
  },
  "persona_insights": {
    "persona_summary": "...",
    "purchase_motivations": ["..."],
    "emotional_triggers": ["..."],
    "recommended_tone": "..."
  }
}
```

---

## 8. Configuration

`config.py`에서 다음 설정을 변경할 수 있습니다:

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `LLM_MODEL` | gpt-4o-mini | 사용할 OpenAI 모델 |
| `EMBEDDING_MODEL` | text-embedding-3-small | 임베딩 모델 |
| `TOP_K_RESULTS` | 5 | RAG 검색 결과 수 |
| `CHUNK_SIZE` | 500 | 문서 청크 크기 |
| `CHUNK_OVERLAP` | 50 | 청크 오버랩 크기 |

---

## 9. Supported Brands

| 브랜드 (한글) | Brand (English) | 톤 |
|---------------|-----------------|-----|
| 설화수 | Sulwhasoo | 고급스럽고 우아함 |
| 라네즈 | LANEIGE | 세련되고 활기참 |
| 헤라 | HERA | 세련되고 당당함 |
| 이니스프리 | innisfree | 자연스럽고 친근함 |
| 아이오페 | IOPE | 과학적이고 신뢰감 |
| 에뛰드 | ETUDE | 발랄하고 즐거움 |
| 에스트라 | AESTURA | 피부과학 전문성 |
| 마몽드 | Mamonde | 꽃의 생명력 |
| 프리메라 | Primera | 자연주의 |
| 에스쁘아 | espoir | 프로페셔널 메이크업 |
| 한율 | HANYUL | 한국 자연 원료 |
| 일리윤 | ILLIYOON | 민감 피부 전문 |

---

## 10. Tech Stack

| 영역 | 기술 | 용도 |
|------|------|------|
| **LLM** | OpenAI GPT-4o-mini | 텍스트 생성, 분석 |
| **Orchestration** | LangChain, LangGraph | Agent 오케스트레이션 |
| **Vector DB** | ChromaDB | 제품 벡터 저장/검색 |
| **Embeddings** | OpenAI text-embedding-3-small | 텍스트 임베딩 |
| **UI** | Streamlit | 웹 인터페이스 |
| **Language** | Python 3.10+ | 개발 언어 |

---

## 11. Key Features

### 11.1 Retry & Fallback 메커니즘
- LLM 응답 실패 시 최대 2회 재시도
- 재시도 실패 시 RAG 결과에서 직접 제품 생성 (Fallback)

### 11.2 중복 제거
- RAG 검색 결과에서 product_id 기준 중복 제거
- 동일 제품의 다중 청크 검색 문제 해결

### 11.3 이미지 URL 자동 매핑
- final_products.json의 image_urls를 벡터 DB 메타데이터에 저장
- 추천 제품에 자동으로 이미지 URL 첨부

---

## 12. License

This project is developed for the Amorepacific AI Innovation Challenge.

---

## 13. Authors

- Agent 10 Team

---

## 14. Appendix: Persona Examples

### P001: 트렌드세터 지영
- **연령대**: 25-29세 여성
- **피부타입**: 복합성
- **피부고민**: 모공, 피지관리, 톤업
- **라이프스타일**: SNS 활발, 신제품 얼리어답터
- **구매트리거**: 인플루언서 추천, 한정판, 신제품

### P002: 워킹맘 수진
- **연령대**: 35-39세 여성
- **피부타입**: 건성
- **피부고민**: 주름, 탄력, 보습
- **라이프스타일**: 바쁜 일상, 효율 중시
- **구매트리거**: 할인, 대용량, 검증된 성분

### P003: 스킨케어 덕후 민서
- **연령대**: 22-25세 여성
- **피부타입**: 민감성
- **피부고민**: 트러블, 진정, 저자극
- **라이프스타일**: 성분 분석 철저, 리뷰 꼼꼼히 확인
- **구매트리거**: 성분 정보, 실사용 리뷰, 샘플 증정

