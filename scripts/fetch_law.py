# -*- coding: utf-8 -*-#
import math
import xmltodict
import requests
from dotenv import load_dotenv
from tqdm import tqdm
import os

# .env 파일에서 환경 변수 로드
load_dotenv()
SERVICE_KEY = os.getenv("OC_ID")

law_dict = {
    "법률": [
        "방위사업법", "군용항공기비행안정성인증에관한법률", "방위산업기술보호법",
        "국방과학기술혁신촉진법", "방위산업발전및지원에관한법률", "국방과학연구소법",
        "민ㆍ군기술협력사업촉진법", "국가를 당사자로 하는 계약에 관한 법률",
        "정부기업예산법", "예산회계에 관한 특례법", "군수품 관리법", "물품관리법"
    ],
    "시행령": [
        "방위사업법시행령", "방위사업청과 그 소속기관직제", "군용항공기 비행안전성 인증에 관한 법률 시행령",
        "방위산업기술보호법 시행령", "국방과학연구소법 시행령", "국방과학기술혁신 촉진법 시행령",
        "방위산업발전및지원에관한법률시행령", "국가를 당사자로 하는 계약에 관한 법률 시행령",
        "정부기업예산법 시행령", "예산회계에 관한 특례법 시행령", "군수품 관리법 시행령", "물품관리법 시행령"
    ],
    "시행규칙": [
        "방위사업법 시행규칙", "방위사업청과 그 소속기관 직제 시행규칙", "군용항공기 비행안전성 인증에 관한 법률 시행규칙",
        "국방과학기술혁신 촉진법 시행규칙", "방위산업발전 및 지원에 관한 법률 시행규칙", "방위산업에 관한 계약사무 처리규칙",
        "방산원가대상물자의 원가계산에 관한 규칙", "방위산업에 관한 착수금 및 중도금 지급규칙",
        "방위사업감독관 직무 등에 관한 규칙", "방위산업기술 보호법 시행규칙", "국가를 당사자로 하는 계약에 관한 법률 시행규칙",
        "방위산업에 관한 계약 사무처리규칙", "방위산업에 관한 착수금 및 중도금 지급규칙",
        "방산원가대상물자의 원가계산에 관한 규칙", "특정물품등의 조달에 관한 국가를 당사자로 하는 계약에 관한 법률 시행령 특례규정",
        "특정물품등의 조달에 관한 국가를 당사자로 하는 계약사무처리 특례규칙", "특정조달을 위한 국가를 당사자로 하는 계약에 관한 법률 시행령 특례규정",
        "특정조달을 위한 국가를 당사자로 하는 계약에 관한 법률 시행 특례규칙", "예산회계법 시행령 임시특례에 관한 규정",
        "군수품 관리법 시행규칙", "물품관리법 시행규칙"
    ]
}

class LawSearch:
    # 상수 정의
    SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
    DETAIL_URL = "https://www.law.go.kr/DRF/lawService.do"
    DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0'}
    
    def __init__(self, type_="JSON", display=100, page=1):
        self.service_key = SERVICE_KEY
        self.target = "law"
        self.type_ = type_.upper()
        self.display = display
        self.page = page
        self.law_id_list = []
        
        # 기본 파라미터
        self.base_params = {
            "OC": self.service_key,
            "target": self.target,
            "type": self.type_
        }

    def _api_request(self, url, params):
        """공통 API 요청 처리"""
        try:
            response = requests.get(url, headers=self.DEFAULT_HEADERS, params=params, timeout=10)
            print(f"Request URL: {response.url}")  # 디버깅
            print(f"Status Code: {response.status_code}")  # 디버깅
            response.raise_for_status()  # HTTP 오류 자동 처리
            
            return response.json() if self.type_ == "JSON" else xmltodict.parse(response.content)
            
        except requests.RequestException as e:
            print(f"API 요청 오류: {e}")
            return None
        except Exception as e:
            print(f"데이터 처리 오류: {e}")
            return None

    def _extract_unique_values(self, items, key_name):
        """리스트에서 특정 키의 고유값들을 추출"""
        return list({item.get(key_name) for item in items if item.get(key_name)})

    def _normalize_law_items(self, law_items):
        """법령 아이템을 리스트 형태로 정규화"""
        if not law_items:
            return []
        return [law_items] if isinstance(law_items, dict) else law_items

    def search_law(self, law_name):
        """법령 검색"""
        params = {
            **self.base_params,
            "query": law_name,
            "display": self.display,
            "page": self.page
        }
        
        data = self._api_request(self.SEARCH_URL, params)
        print(f"Searching for {law_name}: {data}")  # 디버깅 추가
        if not data:
            return []
            
        law_items = data.get('LawSearch', {}).get('law', [])
        return self._normalize_law_items(law_items)

    def collect_all_mst_ids(self):
        """모든 MST ID 수집"""
        self.law_id_list.clear()
        
        for law_type, law_list in law_dict.items():
            print(f"{law_type} 검색 시작... ({len(law_list)}개)")
            
            type_ids = []
            for law_name in tqdm(law_list, desc=f"{law_type} 처리중"):
                law_items = self.search_law(law_name)
                new_ids = self._extract_unique_values(law_items, '법령일련번호')
                type_ids.extend(new_ids)
            
            # 타입별로도 중복 제거
            unique_type_ids = list(set(type_ids))
            self.law_id_list.extend(unique_type_ids)
            print(f"{law_type} 완료: {len(unique_type_ids)}개")
        
        # 전체 중복 제거
        self.law_id_list = list(set(self.law_id_list))
        print(f"총 MST ID 수집: {len(self.law_id_list)}개 (중복 제거 후)")
        return self.law_id_list

    def get_law_details(self, mst_ids=None):
        """상세 법령 조회"""
        if mst_ids is None:
            mst_ids = self.law_id_list
            
        if not mst_ids:
            print("조회할 MST ID가 없습니다.")
            return {}
            
        details = {}
        successful_requests = 0
        
        for mst_id in tqdm(mst_ids, desc="상세 법령 수집중"):
            params = {**self.base_params, "MST": mst_id}
            data = self._api_request(self.DETAIL_URL, params)
            
            if data:
                details[mst_id] = data
                successful_requests += 1
                
        print(f"총 {successful_requests}/{len(mst_ids)}개 법령 상세 수집 완료")
        return details


if __name__ == "__main__":
    search = LawSearch()
    # 한 개 MST 테스트
    mst_ids = ['276309']  # 방위사업법 MST ID
    law_details = search.get_law_details(mst_ids)
    print(f"수집된 법령 수: {len(law_details)}")
    # 저장
    from save_law import save_law_details
    save_law_details(law_details)