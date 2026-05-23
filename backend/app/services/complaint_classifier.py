import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DETAIL_RULES_PATH = BASE_DIR / "ai" / "data" / "detail_rules.json"


def classify_complaint(text: str) -> dict:
    """
    민원 내용을 보고 세부 민원 유형을 분류하는 함수
    ai/data/detail_rules.json의 키워드 규칙을 사용한다.
    """

    with open(DETAIL_RULES_PATH, "r", encoding="utf-8") as f:
        detail_rules = json.load(f)

    best_label = "general_complaint"
    best_score = 0
    matched_keywords = []

    for category, labels in detail_rules.items():
        for label, rule_value in labels.items():

            # 기타 항목처럼 구조가 다른 경우 처리
            if isinstance(rule_value, dict):
                keywords = rule_value.get("keywords", [])
            else:
                keywords = rule_value

            current_matches = []

            for keyword in keywords:
                if keyword in text:
                    current_matches.append(keyword)

            if len(current_matches) > best_score:
                best_score = len(current_matches)
                best_label = label
                matched_keywords = current_matches

    if best_score == 0:
        return {
            "complaint_type": "general_complaint",
            "type_confidence": 0.50,
            "matched_keywords": []
        }

    confidence = min(0.95, 0.60 + best_score * 0.10)

    return {
        "complaint_type": best_label,
        "type_confidence": round(confidence, 2),
        "matched_keywords": matched_keywords
    }