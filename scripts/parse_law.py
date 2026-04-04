import json
import re
from typing import List, Dict, Any

def parse_law_articles(law_data: Dict[str, Any], law_name: str) -> List[Dict[str, Any]]:
    """
    법령 데이터를 조문 단위로 파싱하여 law_articles 형식으로 변환
    """
    articles = []
    
    if '법령' not in law_data or '조문' not in law_data['법령']:
        return articles
    
    jo_mun_list = law_data['법령']['조문'].get('조문단위', [])
    
    for idx, jo_mun in enumerate(jo_mun_list):
        if jo_mun.get('조문여부') != '조문':
            continue  # 전문 등 조문이 아닌 것은 skip
        
        article = {
            'article_key': f"{law_name}|{jo_mun['조문번호']}",
            'article_no': jo_mun['조문번호'],
            'paragraph_no': None,
            'item_no': None,
            'subitem_no': None,
            'title': jo_mun.get('조문제목'),
            'full_text': jo_mun['조문내용'],
            'normalized_text': normalize_text(jo_mun['조문내용']),
            'display_order': idx + 1
        }
        
        articles.append(article)
        
        # 항 파싱
        if '항' in jo_mun:
            hang_list = jo_mun['항'] if isinstance(jo_mun['항'], list) else [jo_mun['항']]
            for hang in hang_list:
                hang_article = article.copy()
                hang_article['paragraph_no'] = hang['항번호']
                hang_article['full_text'] = hang['항내용']
                hang_article['normalized_text'] = normalize_text(hang['항내용'])
                hang_article['article_key'] = f"{law_name}|{jo_mun['조문번호']}|{hang['항번호']}"
                articles.append(hang_article)
                
                # 호 파싱
                if '호' in hang:
                    ho_list = hang['호'] if isinstance(hang['호'], list) else [hang['호']]
                    for ho in ho_list:
                        ho_article = hang_article.copy()
                        ho_article['item_no'] = ho['호번호']
                        ho_article['full_text'] = ho['호내용']
                        ho_article['normalized_text'] = normalize_text(ho['호내용'])
                        ho_article['article_key'] = f"{law_name}|{jo_mun['조문번호']}|{hang['항번호']}|{ho['호번호']}"
                        articles.append(ho_article)
                        
                        # 목 파싱 (호 안에 목이 있을 수 있음)
                        if '목' in ho:
                            mok_list = ho['목'] if isinstance(ho['목'], list) else [ho['목']]
                            for mok in mok_list:
                                mok_article = ho_article.copy()
                                mok_article['subitem_no'] = mok['목번호']
                                mok_article['full_text'] = mok['목내용']
                                mok_article['normalized_text'] = normalize_text(mok['목내용'])
                                mok_article['article_key'] = f"{law_name}|{jo_mun['조문번호']}|{hang['항번호']}|{ho['호번호']}|{mok['목번호']}"
                                articles.append(mok_article)
    
    return articles

def normalize_text(text: str) -> str:
    """
    텍스트 정규화: 불필요한 공백, 특수문자 제거 등
    """
    # 기본 정규화
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def load_and_parse_law_file(filepath: str) -> List[Dict[str, Any]]:
    """
    JSON 파일을 로드하고 조문 파싱
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_articles = []
    for mst_id, law_data in data.items():
        law_name = law_data.get('법령', {}).get('기본정보', {}).get('법령명_한글', 'Unknown')
        articles = parse_law_articles(law_data, law_name)
        all_articles.extend(articles)
    
    return all_articles

if __name__ == "__main__":
    from example.save_law import save_parsed_articles

    # 테스트
    filepath = 'data/law_details_20260405_013655.json'
    articles = load_and_parse_law_file(filepath)
    print(f"파싱된 조문 수: {len(articles)}")
    for art in articles[:5]:  # 처음 5개만 출력
        print(art)

    saved_path = save_parsed_articles(articles)
    print(f"Parsed articles saved to: {saved_path}")