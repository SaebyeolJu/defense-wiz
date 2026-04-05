import httpx
import xmltodict
from typing import Dict, List, Any, Optional
from app.core.config import settings

class IngestionService:
    SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
    DETAIL_URL = "https://www.law.go.kr/DRF/lawService.do"

    def __init__(self):
        self.oc_id = settings.OC_ID

    async def _fetch(self, url: str, params: Dict[str, Any], use_xml: bool = False) -> Optional[Dict[str, Any]]:
        """API 요청 공통 처리 (Async)"""
        params["OC"] = self.oc_id
        # 기본적으로 JSON 요청 (상세 정보는 XML로만 오는 경우가 있음)
        if not use_xml:
            params["type"] = "JSON"
        else:
            params["type"] = "XML"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=20.0)
                response.raise_for_status()
                
                if use_xml:
                    return xmltodict.parse(response.content)
                return response.json()
            except Exception as e:
                print(f"Error fetching from {url}: {e}")
                return None

    async def search_law(self, query: str) -> List[Dict[str, Any]]:
        """법령 검색 (명칭 기반)"""
        params = {
            "target": "law",
            "query": query,
        }
        data = await self._fetch(self.SEARCH_URL, params)
        if not data:
            return []
        
        law_items = data.get("LawSearch", {}).get("law", [])
        if isinstance(law_items, dict):
            return [law_items]
        return law_items

    async def get_law_detail(self, mst_id: str) -> Optional[Dict[str, Any]]:
        """법령 상세 조회 (MST ID 기반)"""
        # 상세 데이터는 XML 포맷이 더 많은 조문 정보를 포함하므로 XML로 수집 후 dict 변환 권장
        params = {
            "target": "law",
            "MST": mst_id,
        }
        return await self._fetch(self.DETAIL_URL, params, use_xml=True)

ingestion_service = IngestionService()
