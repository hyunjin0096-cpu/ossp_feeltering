import json
from pathlib import Path


DEPARTMENT_RULES_PATH = Path(__file__).resolve().parent / "data" / "department_rules.json"


class DepartmentRecommender:
    def __init__(self):
        with open(DEPARTMENT_RULES_PATH, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def recommend(self, detail_label: str) -> dict:
        department_info = self.rules.get(detail_label)

        if department_info is None:
            department_info = self.rules.get("general_complaint") or self.rules.get("etc")

        return department_info


if __name__ == "__main__":
    recommender = DepartmentRecommender()

    detail_label = "illegal_parking"
    result = recommender.recommend(detail_label)

    print(result)
