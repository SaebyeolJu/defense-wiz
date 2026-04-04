import json
import os
from datetime import datetime

def _ensure_dir(output_dir: str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def save_json(data, filename: str, output_dir: str = "data") -> str:
    """
    데이터를 JSON 파일로 저장한다.
    """
    _ensure_dir(output_dir)

    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"JSON 데이터가 {filepath}에 저장되었습니다.")
    return filepath


def save_law_details(law_details, output_dir="data") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"law_details_{timestamp}.json"
    return save_json(law_details, filename, output_dir)


def save_parsed_articles(articles, output_dir="data") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"law_articles_{timestamp}.json"
    return save_json(articles, filename, output_dir)

# 사용 예시
if __name__ == "__main__":
    # 테스트 데이터
    sample_data = {
        "276309": {
            "법령명": "방위사업법",
            "조문": [{"조문번호": "1", "조문내용": "테스트"}]
        }
    }
    save_law_details(sample_data)