# DefenseWiz 개발 명세서 (Codex 작업용)

## 1. 프로젝트 개요

DefenseWiz는 **대한민국 방위산업 관련 법령을 기반으로 질의응답, 개정 전후 비교, 조문 기반 학습 기능을 제공하는 법령 특화 서비스**다.

이 프로젝트는 일반적인 "LLM 파인튜닝 챗봇"이 아니라, 아래 구조를 따르는 **법령 특화 RAG + 버전 비교 플랫폼**으로 개발한다.

- 법령 원문 수집
- 법령 버전 관리
- 조문 단위 구조화
- 벡터 검색 기반 질의응답
- 개정 전/후 diff 비교
- 조문 기반 문제 생성
- 사용자 학습 기록 관리

핵심 원칙:

1. **LLM은 판단자가 아니라 설명자다.**
2. **최신성은 재학습이 아니라 데이터 파이프라인으로 보장한다.**
3. **개정 비교는 RAG 단독이 아니라 버전 관리 + diff 엔진으로 처리한다.**
4. **PostgreSQL이 정본(source of truth), Qdrant는 검색 전용 인덱스다.**

---

## 2. MVP 범위

### 포함
- 방위산업 관련 법령 수집 및 저장
- 최신 법령 기준 질의응답
- 개정 전/후 법령 비교
- 조문 기반 문제 생성
- 사용자별 문제 풀이/오답노트 저장

### 제외
- 커뮤니티 게시판
- 댓글/좋아요/신고
- 푸시 알림
- 관리자 대시보드 고도화
- 대규모 랭킹/소셜 기능

---

## 3. 기술 스택

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Python 3.11+
- SQLAlchemy
- Pydantic

### Database
- PostgreSQL

### Vector Search
- Qdrant

### Scheduler / Batch
- APScheduler

### Optional (후순위)
- Redis
- Celery/RQ

### Infra
- Docker
- docker-compose

---

## 4. 아키텍처 원칙

### 데이터 저장 역할

#### PostgreSQL
다음 데이터를 저장한다.
- 법령 기본 정보
- 법령 버전 정보
- 조문 원문
- 개정 전/후 diff
- 사용자 정보
- 퀴즈/오답노트
- 질의응답 로그

#### Qdrant
다음 데이터만 저장한다.
- 임베딩 벡터
- 검색용 chunk text
- 최소 metadata
  - article_id
  - version_id
  - law_name
  - article_no
  - effective_date
  - is_current

### 중요
- 임베딩은 Qdrant가 생성하지 않는다.
- 임베딩은 Python 애플리케이션에서 생성한다.
- Qdrant는 벡터 저장 및 유사도 검색만 담당한다.

---

## 5. 시스템 모듈 구성

### 5.1 Ingestion Module
역할:
- 국가법령정보센터 API에서 법령 수집
- 대상 법령 화이트리스트 관리
- 변경 여부 감지

### 5.2 Parsing Module
역할:
- 법령 원문 정규화
- 조/항/호/목 단위 파싱
- 부칙/별표 분리
- article_key 생성

### 5.3 Indexing Module
역할:
- 조문 chunk 생성
- 임베딩 생성
- Qdrant upsert

### 5.4 QA Module
역할:
- 질문 유형 분류
- Qdrant 검색
- PostgreSQL 상세 조회
- 근거 기반 답변 생성

### 5.5 Compare Module
역할:
- 개정 전/후 버전 선택
- article_key 기반 매핑
- diff 조회 또는 생성
- 변경 요약 생성

### 5.6 Quiz Module
역할:
- 조문 기반 문제 생성
- 사용자 답안 채점
- 오답노트 저장

### 5.7 User Module
역할:
- 회원가입/로그인
- 학습 기록 저장
- 퀴즈 시도 이력 저장

---

## 6. 질문 유형 분류

사용자 질문은 아래 4가지로 라우팅한다.

### A. 일반 질의응답
예:
- 국산화정보체계 책임 기관이 어디야?
- 방산업체 지정 요건이 뭐야?

처리:
- QA Module

### B. 개정 전/후 비교
예:
- 개정 전후 차이 알려줘
- 최신 개정에서 뭐가 달라졌어?

처리:
- Compare Module

### C. 절차/요건 정리
예:
- 절차를 정리해줘
- 요건만 요약해줘

처리:
- QA Module + structured extraction

### D. 문제 생성/학습
예:
- 이 조문으로 문제 만들어줘
- 오답노트 보여줘

처리:
- Quiz Module

---

## 7. DB 스키마 초안

### 7.1 laws
법령 마스터

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 법령 ID |
| law_name | varchar | 법령명 |
| law_type | varchar | 법률/시행령/시행규칙/훈령/고시 |
| ministry | varchar | 소관 부처 |
| source_url | text | 원문 출처 |
| is_active | boolean | 활성 여부 |
| created_at | timestamp | 생성 시각 |
| updated_at | timestamp | 수정 시각 |

### 7.2 law_versions
법령 버전 정보

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 버전 ID |
| law_id | bigint FK | laws.id |
| version_label | varchar | 버전 라벨 |
| promulgation_date | date | 공포일 |
| effective_date | date | 시행일 |
| amended_type | varchar | 제정/일부개정/전부개정/폐지 |
| is_current | boolean | 현행 여부 |
| previous_version_id | bigint nullable | 이전 버전 ID |
| raw_hash | varchar | 원문 해시 |
| created_at | timestamp | 생성 시각 |

### 7.3 law_articles
조문 구조 저장

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 조문 ID |
| law_version_id | bigint FK | law_versions.id |
| article_key | varchar | 버전 간 비교용 안정 키 |
| article_no | varchar | 조 번호 |
| paragraph_no | varchar nullable | 항 번호 |
| item_no | varchar nullable | 호 번호 |
| subitem_no | varchar nullable | 목 번호 |
| title | varchar nullable | 조 제목 |
| full_text | text | 원문 |
| normalized_text | text | 정규화 텍스트 |
| display_order | int | 정렬 순서 |
| created_at | timestamp | 생성 시각 |

### 7.4 law_chunks
검색용 청크

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 청크 ID |
| article_id | bigint FK | law_articles.id |
| chunk_text | text | 검색용 텍스트 |
| chunk_order | int | 순서 |
| qdrant_point_id | varchar nullable | Qdrant point id |
| created_at | timestamp | 생성 시각 |

### 7.5 law_version_diffs
개정 전/후 비교 데이터

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | diff ID |
| law_id | bigint FK | laws.id |
| old_version_id | bigint FK | 이전 버전 |
| new_version_id | bigint FK | 새 버전 |
| article_key | varchar | 비교 키 |
| change_type | varchar | added/deleted/modified/unchanged |
| old_article_id | bigint nullable | 이전 조문 |
| new_article_id | bigint nullable | 새 조문 |
| old_text | text nullable | 이전 원문 |
| new_text | text nullable | 새 원문 |
| diff_summary | text nullable | 요약 |
| changed_fields | jsonb nullable | 변경 필드 정보 |
| created_at | timestamp | 생성 시각 |

### 7.6 users

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 유저 ID |
| email | varchar unique | 이메일 |
| password_hash | varchar | 비밀번호 해시 |
| nickname | varchar | 닉네임 |
| role | varchar | user/admin |
| created_at | timestamp | 생성 시각 |

### 7.7 qa_logs

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 로그 ID |
| user_id | bigint nullable FK | users.id |
| intent_type | varchar | qa/compare/summary/quiz |
| question | text | 사용자 질문 |
| retrieved_chunk_ids | jsonb | 검색 결과 chunk ids |
| final_answer | text | 최종 답변 |
| confidence_score | varchar | high/medium/low |
| created_at | timestamp | 생성 시각 |

### 7.8 quiz_questions

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 문제 ID |
| article_id | bigint FK | source law article |
| question_type | varchar | mcq/ox/blank |
| question_text | text | 문제 |
| choices_json | jsonb nullable | 보기 |
| answer_json | jsonb | 정답 |
| explanation_text | text | 해설 |
| difficulty | varchar nullable | 난이도 |
| created_at | timestamp | 생성 시각 |

### 7.9 quiz_attempts

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| id | bigint PK | 시도 ID |
| user_id | bigint FK | users.id |
| question_id | bigint FK | quiz_questions.id |
| user_answer | jsonb | 사용자 답 |
| is_correct | boolean | 정답 여부 |
| feedback | text nullable | 피드백 |
| attempted_at | timestamp | 시도 시각 |

---

## 8. article_key 설계 규칙

개정 전/후 비교를 위해 article_key는 버전이 달라도 동일 조문 위치를 식별할 수 있어야 한다.

예시:
- 방위사업법|제28조
- 방위사업법|제28조|1항
- 방위사업법|제28조|1항|2호

규칙:
1. 법령명 포함
2. 조/항/호/목을 계층적으로 연결
3. 버전 ID는 포함하지 않음
4. 비교 시 stable identifier로 사용

---

## 9. Qdrant payload 설계

예시:

```json
{
  "article_id": 401,
  "version_id": 33,
  "law_name": "방위사업법",
  "article_no": "제28조",
  "effective_date": "2025-12-15",
  "is_current": true,
  "chunk_order": 1
}
```

원칙:
- 검색에 필요한 최소 메타데이터만 넣는다.
- 유저 정보는 넣지 않는다.
- diff 전체 데이터는 넣지 않는다.
- 법령 구조 전체를 payload에 복제하지 않는다.

---

## 10. 법령 수집 및 업데이트 파이프라인

### 목적
최신 법령을 자동 반영하고, 검색 인덱스와 비교 데이터를 유지한다.

### 배치 주기
- 하루 1회 또는 2회

### 처리 단계
1. 대상 법령 화이트리스트 조회
2. 국가법령정보센터 API 호출
3. 기존 raw_hash / version 비교
4. 변경된 법령만 처리
5. 새 law_versions 저장
6. law_articles 파싱 및 저장
7. law_chunks 생성
8. 임베딩 생성
9. Qdrant upsert
10. old/new version diff 생성
11. 회귀 테스트 실행

### 주의
- 개정 시 모델 재학습을 하지 않는다.
- 변경된 법령에 대해 **재색인(re-indexing)** 만 수행한다.

---

## 11. 일반 질의응답 파이프라인

### 입력
사용자 질문

### 처리 흐름
1. intent 분류
2. 질문 정규화
3. 질문 임베딩 생성
4. Qdrant 검색 (top-k)
5. 검색 결과 article_id / version_id 확보
6. PostgreSQL에서 조문/시행일/버전 상세 조회
7. structured extraction 수행
   - 주체
   - 행위
   - 조건
   - 예외
8. LLM 설명 생성
9. 응답 검증
10. 최종 응답 반환

### 응답 형식
- 결론
- 근거 법령명
- 조문 번호
- 시행일
- 원문 일부
- 쉬운 설명
- 주의사항
- confidence

### 제한 원칙
- 근거 없는 답변 금지
- 제공된 조문 밖 상식 보충 금지
- 법률 자문형 판단 금지

---

## 12. 개정 전/후 비교 파이프라인

### 목적
일반 RAG가 아니라 버전 비교 기반으로 시간순 차이를 설명한다.

### 처리 흐름
1. intent = compare 판별
2. 대상 법령 식별
3. 비교 기준 결정
   - 최신 전후
   - 특정 날짜 기준
   - 특정 버전 기준
4. old_version / new_version 선택
5. law_version_diffs 조회
6. 변경 조문 목록 정렬
7. LLM이 diff_summary 기반 설명 생성
8. 비교 응답 반환

### 응답 형식
- 비교 대상 법령
- old version 시행일
- new version 시행일
- 변경 조문 목록
- old/new 원문 비교
- 핵심 차이 요약
- 실무 의미

### 중요 원칙
- 비교 기능은 Qdrant 검색 중심으로 풀지 않는다.
- 버전 선택과 diff 비교는 PostgreSQL 중심으로 처리한다.

---

## 13. 문제 생성 파이프라인

### 목적
특정 조문을 기준으로 학습용 문제를 생성한다.

### 처리 흐름
1. source article 선택
2. 조문 anchor 기반 문제 생성
3. 문제 저장
4. 사용자 답안 제출
5. 자동 채점
6. 피드백 생성
7. 오답노트 저장

### 문제 생성 규칙
- 특정 article_id에 anchored 되어야 한다.
- 정답은 1개여야 한다.
- 해설에는 근거 조문이 포함되어야 한다.
- 시행일 기준이 포함되어야 한다.

---

## 14. API 설계 초안

### Auth
- POST /auth/signup
- POST /auth/login
- GET /auth/me

### Laws
- GET /laws
- GET /laws/{law_id}
- GET /laws/{law_id}/versions
- GET /articles/{article_id}

### QA
- POST /qa/ask
- GET /qa/logs

### Compare
- POST /compare/law-version

### Quiz
- POST /quiz/generate
- POST /quiz/submit
- GET /quiz/wrong-notes

### Admin / Batch
- POST /admin/sync-laws
- POST /admin/reindex
- GET /admin/job-status

---

## 15. 백엔드 폴더 구조 제안

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      logging.py
    db/
      session.py
      base.py
      models/
        laws.py
        versions.py
        articles.py
        diffs.py
        users.py
        quiz.py
        qa_logs.py
    schemas/
      auth.py
      law.py
      qa.py
      compare.py
      quiz.py
    api/
      v1/
        auth.py
        laws.py
        qa.py
        compare.py
        quiz.py
        admin.py
    services/
      ingestion_service.py
      parser_service.py
      chunk_service.py
      embedding_service.py
      qdrant_service.py
      qa_service.py
      compare_service.py
      quiz_service.py
      user_service.py
    repositories/
      law_repository.py
      version_repository.py
      article_repository.py
      diff_repository.py
      user_repository.py
      quiz_repository.py
    workers/
      sync_laws.py
      reindex_laws.py
      generate_diffs.py
    utils/
      text_normalizer.py
      article_key.py
      diff_utils.py
```

---

## 16. 프론트엔드 폴더 구조 제안

```text
frontend/
  app/
    page.tsx
    qa/page.tsx
    compare/page.tsx
    quiz/page.tsx
    laws/[id]/page.tsx
    login/page.tsx
  components/
    qa/
    compare/
    quiz/
    laws/
    common/
  lib/
    api.ts
    auth.ts
    utils.ts
  types/
    law.ts
    qa.ts
    compare.ts
    quiz.ts
```

---

## 17. 개발 순서

### 1단계
- PostgreSQL schema 구현
- SQLAlchemy model 구현
- 법령 1개 수집 PoC
- 조문 파싱 구현

### 2단계
- chunk 생성
- 임베딩 생성 서비스 구현
- Qdrant 연동
- 검색 테스트

### 3단계
- QA API 구현
- structured extraction 구현
- LLM 기반 설명 생성

### 4단계
- compare API 구현
- old/new version 선택
- law_version_diffs 생성 및 조회

### 5단계
- quiz generate / submit 구현
- 사용자 학습 기록 저장

### 6단계
- scheduler 배치 구현
- 자동 업데이트 파이프라인 구축
- 회귀 테스트 추가

---

## 18. 개발 우선순위

### 최우선
1. 데이터 구조
2. 버전 관리
3. 법령 수집
4. 검색 가능 구조

### 그 다음
5. 일반 QA
6. 개정 비교
7. 문제 생성
8. 사용자 기록

### 후순위
9. Redis
10. 커뮤니티
11. 알림
12. 운영 고도화

---

## 19. Codex 작업 지침

### 구현 시 반드시 지킬 것
1. Qdrant를 메인 DB처럼 다루지 말 것
2. PostgreSQL을 정본 데이터 저장소로 유지할 것
3. 비교 기능은 RAG만으로 처리하지 말 것
4. article_key 기반 diff 설계를 우선 구현할 것
5. 임베딩은 Python 애플리케이션 레벨에서 생성할 것
6. 법령 개정 시 전체 재학습이 아니라 증분 업데이트로 처리할 것
7. 각 서비스는 가능한 한 repository/service 구조로 분리할 것

### 답변 품질 관련 규칙
1. 근거 없는 답변 금지
2. 검색 결과 밖 정보 보충 금지
3. 법률 자문형 단정 금지
4. 시행일 및 버전 정보를 항상 고려할 것

---

## 20. 1차 구현 목표

### 1차 완료 조건
아래 시나리오가 동작하면 1차 성공으로 본다.

1. 방위사업법 1개 이상 수집 가능
2. 조문 단위 저장 가능
3. Qdrant 검색 가능
4. 사용자 질문에 대해 관련 조문 검색 가능
5. PostgreSQL에서 조문 상세 조회 가능
6. LLM이 근거 기반 설명 가능
7. 최신 버전과 이전 버전 비교 가능
8. 특정 조문 기반 문제 생성 가능

---

## 21. 최종 요약

DefenseWiz는 다음 구조로 개발한다.

- **PostgreSQL**: 법령 정본, 버전, 조문, diff, 사용자, 퀴즈, 로그 저장
- **Qdrant**: 임베딩 벡터 검색 전용
- **FastAPI**: API 및 파이프라인 제어
- **Next.js**: 사용자 서비스 UI
- **APScheduler**: 법령 업데이트 자동화

핵심 엔진은 3개다.

1. 일반 QA 엔진 (RAG 기반)
2. 개정 비교 엔진 (version diff 기반)
3. 문제 생성 엔진 (article anchored)

이 문서를 기준으로 Codex는 우선 다음부터 구현한다.

1. PostgreSQL schema
2. 법령 ingestion
3. parser
4. embedding + Qdrant indexing
5. QA API
6. compare API
7. quiz API

