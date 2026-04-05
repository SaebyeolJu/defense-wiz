import logging
import asyncio
import requests
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma3:4b"

    async def ask_question(self, question: str) -> str:
        # 1. 질문 임베딩 생성
        logger.info(f"Generating embedding for question: {question}")
        query_vector = embedding_service.generate_embedding(question)
        
        # 2. Qdrant에서 관련 조항 검색
        logger.info("Searching Qdrant for context")
        search_results = qdrant_service.search(query_vector=query_vector, limit=5)
        
        if not search_results:
            return "관련된 법령 조항을 찾을 수 없습니다."

        # 3. 검색된 결과 포매팅
        context_parts = []
        for point in search_results:
            payload = point.payload
            law_name = payload.get("law_name", "알 수 없는 법령")
            article_no = payload.get("article_no", "")
            chunk_text = payload.get("chunk_text", "")
            context_parts.append(f"[{law_name} {article_no}]\n{chunk_text}")
            
        context_str = "\n\n".join(context_parts)
        
        # 4. 시스템 프롬프트 구성
        prompt = f"""당신은 대한민국 국방, 방산 분야 법령에 통달한 법률 전문가 AI입니다. 
주어진 법령 조항(Context)을 바탕으로 사용자의 질문(Question)에 대해 정확하고 객관적으로 답변해 주십시오. 
없는 내용을 지어내지 말고 제공된 Context 범위 내에서만 답변하며, 답변 시 근거가 되는 조문 번호를 함께 언급해 주십시오.

[Context]
{context_str}

[Question]
{question}

[Answer]
"""

        # 5. 로컬 Ollama API 비동기 호출 (requests 라이브러리 차단 방지)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        logger.info(f"Calling Ollama model '{self.model_name}'")
        try:
            response = await asyncio.to_thread(
                requests.post, self.ollama_url, json=payload, timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "답변 추출에 실패했습니다.")
        except Exception as e:
            logger.error(f"Ollama API 호출 중 오류 발생: {e}")
            return f"오류가 발생했습니다: {str(e)}"

qa_service = QAService()
