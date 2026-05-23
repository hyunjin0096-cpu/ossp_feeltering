import json
from pathlib import Path


# 현재 파일 위치:
# backend/app/services/department_recommender.py
#
# parents[0] = services
# parents[1] = app
# parents[2] = backend
# parents[3] = Feeltering
BASE_DIR = Path(__file__).resolve().parents[3]

DEPARTMENT_RULES_PATH = BASE_DIR / "ai" / "data" / "department_rules.json"


def recommend_department(complaint_type: str) -> dict:
    """
    민원 유형 라벨을 입력받아 ai/data/department_rules.json에서
    담당 부서 정보를 찾아 반환하는 함수
    """

    with open(DEPARTMENT_RULES_PATH, "r", encoding="utf-8") as f:
        department_rules = json.load(f)

    result = department_rules.get(
        complaint_type,
        department_rules["etc"]
    )

    return {
        "recommended_department": result["department"],
        "department_reason": result["reason"],
        "contact": result["contact"],
        "website": result["website"],
        "required_documents": result["required_documents"],
        "extra_info": result["extra_info"]
    }