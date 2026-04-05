import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.db.models.laws import Law, LawVersion
from app.db.models.articles import LawArticle

class ParserService:
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
            
        # 1. 원문자 기호(①, ②...)를 일반 숫자와 마침표로 치환 (예: ① -> 1. )
        circle_map = {
            '①': '1. ', '②': '2. ', '③': '3. ', '④': '4. ', '⑤': '5. ',
            '⑥': '6. ', '⑦': '7. ', '⑧': '8. ', '⑨': '9. ', '⑩': '10. ',
            '⑪': '11. ', '⑫': '12. ', '⑬': '13. ', '⑭': '14. ', '⑮': '15. ',
            '⑯': '16. ', '⑰': '17. ', '⑱': '18. ', '⑲': '19. ', '⑳': '20. '
        }
        for k, v in circle_map.items():
            text = text.replace(k, v)
        
        # 2. 특수 제어 문자 제거 (공백, 줄바꿈 제외)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 3. 구두점 뒤 띄어쓰기 교정 (예: "개선,방위" -> "개선, 방위")
        text = re.sub(r'([,;])(?=[^\s\d])', r'\1 ', text)
        text = re.sub(r'([.])(?=[\u3131-\u3163\uAC00-\uD7A3a-zA-Z])', r'\1 ', text)

        # 4. 중복 공백 다중 스페이스 하나로 병합 및 trim
        return re.sub(r'\s+', ' ', text.strip())

    def normalize_circle_number(self, text: str) -> str:
        """원문자(⓪~㊿)를 아라비아 숫자 텍스트로 변환"""
        if not text:
            return ""
        
        result = []
        for char in text:
            code = ord(char)
            if 0x2460 <= code <= 0x2473:      # ①(1) ~ ⑳(20)
                result.append(str(code - 0x2460 + 1))
            elif 0x3251 <= code <= 0x325F:    # ㉑(21) ~ ㉟(35)
                result.append(str(code - 0x3251 + 21))
            elif 0x32B1 <= code <= 0x32BF:    # ㊱(36) ~ ㊿(50)
                result.append(str(code - 0x32B1 + 36))
            elif code == 0x24EA:              # ⓪(0)
                result.append("0")
            else:
                result.append(char)
                
        return "".join(result)
    def _get_text(self, item: Any) -> str:
        """xmltodict로 변환된 dict 또는 string에서 텍스트 추출"""
        if item is None:
            return ""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return item.get("#text", "")
        return str(item)

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """YYYYMMDD -> date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y%m%d").date()
        except Exception:
            return None

    def create_article_key(self, law_name: str, article_no: str, paragraph: str = None, item: str = None, subitem: str = None) -> str:
        key_parts = [law_name, article_no]
        if paragraph: key_parts.append(paragraph)
        if item: key_parts.append(item)
        if subitem: key_parts.append(subitem)
        return "|".join(key_parts)

    def parse_law_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        IngestionService에서 받은 dict를 파싱하여 모델 객체 리스트 반환
        """
        law_info = data.get("법령", {})
        basic_info = law_info.get("기본정보", {})
        
        # MST ID (법령일련번호) 추출 - @법령키 또는 다른 필드 확인 필요
        # get_law_detail 시 넘겼던 MST ID는 사실 XML 내부에 직접 없을 수도 있으므로 
        # 호출부에서 넘겨받거나 @법령키 혹은 기본정보 내 ID 활용
        mst_id = basic_info.get("법령ID", "0") # 임시로 법령 ID 사용하거나 외부에서 주입
        
        # 1. Law 객체 생성
        law_name = self._get_text(basic_info.get("법령명_한글"))
        law = Law(
            id=int(mst_id) if mst_id.isdigit() else 0,
            law_name=law_name,
            law_type=self._get_text(basic_info.get("법종구분")),
            ministry=self._get_text(basic_info.get("소관부처")),
            source_url=f"https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={mst_id}"
        )

        # 2. LawVersion 객체 생성
        # XML에서는 '공포번호'와 '제개정구분' 등을 사용
        version = LawVersion(
            id=law.id, 
            law_id=law.id,
            version_label=self._get_text(basic_info.get("공포번호", "최신")),
            promulgation_date=self.parse_date(self._get_text(basic_info.get("공포일자"))),
            effective_date=self.parse_date(self._get_text(basic_info.get("시행일자"))),
            amended_type=self._get_text(basic_info.get("제개정구분")),
            is_current=True
        )

        # 3. 조문(Articles) 파싱
        articles = []
        jo_list = law_info.get("조문", {}).get("조문단위", [])
        if isinstance(jo_list, dict):
            jo_list = [jo_list]
        
        for idx, jo in enumerate(jo_list):
            if self._get_text(jo.get("조문여부")) != "조문":
                continue

            # 기본 조문 정보
            article_no = self._get_text(jo.get("조문번호"))
            title = self._get_text(jo.get("조문제목"))
            full_text = self._get_text(jo.get("조문내용", ""))
            
            # 조문 본체 추가
            articles.append(LawArticle(
                article_key=self.create_article_key(law_name, article_no),
                article_no=article_no,
                title=title,
                full_text=full_text,
                normalized_text=self.normalize_text(full_text),
                display_order=idx * 1000
            ))

            # 항(Paragraph) 파싱
            hang_list = jo.get("항", [])
            if not hang_list: continue
            if isinstance(hang_list, dict): hang_list = [hang_list]
            
            for h_idx, hang in enumerate(hang_list):
                hang_no = self.normalize_circle_number(self._get_text(hang.get("항번호")))
                hang_text = self._get_text(hang.get("항내용"))
                if not hang_text: continue

                articles.append(LawArticle(
                    article_key=self.create_article_key(law_name, article_no, hang_no),
                    article_no=article_no,
                    paragraph_no=hang_no,
                    full_text=hang_text,
                    normalized_text=self.normalize_text(hang_text),
                    display_order=(idx * 1000) + (h_idx + 1) * 10
                ))

                # 호(Item) 파싱
                ho_list = hang.get("호", [])
                if not ho_list: continue
                if isinstance(ho_list, dict): ho_list = [ho_list]
                
                for i_idx, ho in enumerate(ho_list):
                    ho_no = self._get_text(ho.get("호번호"))
                    ho_text = self._get_text(ho.get("호내용"))
                    if not ho_text: continue

                    articles.append(LawArticle(
                        article_key=self.create_article_key(law_name, article_no, hang_no, ho_no),
                        article_no=article_no,
                        paragraph_no=hang_no,
                        item_no=ho_no,
                        full_text=ho_text,
                        normalized_text=self.normalize_text(ho_text),
                        display_order=(idx * 1000) + (h_idx + 1) * 10 + (i_idx + 1)
                    ))

        return {
            "law": law,
            "version": version,
            "articles": articles
        }

parser_service = ParserService()
