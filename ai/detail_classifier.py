import json


DETAIL_RULES_PATH = "./data/detail_rules.json"


class DetailClassifier:
    def __init__(self):
        with open(DETAIL_RULES_PATH, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def classify(self, text: str, category: str) -> str:
        """
        text: 사용자가 입력한 민원 문장
        category: 1차 AI 모델이 예측한 대분류
                  예: 교통 / 환경 / 안전 / 기타

        return: 세부 label
                예: illegal_parking, road_damage, waste_cleaning
        """

        # 해당 대분류 규칙 가져오기
        category_rules = self.rules.get(category)

        # 대분류가 detail_rules.json에 없으면 기타 처리
        if category_rules is None:
            return "general_complaint"

        # 기타는 현재 JSON 구조가 다르므로 바로 general_complaint 반환
        if category == "기타":
            return "general_complaint"

        # 세부 label별 키워드 검사
        for detail_label, keywords in category_rules.items():
            for keyword in keywords:
                if keyword in text:
                    return detail_label

        # 키워드가 하나도 안 잡힌 경우 대분류별 기본 label 반환
        if category == "교통":
            return "traffic_general"
        elif category == "환경":
            return "environment_general"
        elif category == "안전":
            return "safety_general"
        else:
            return "general_complaint"


if __name__ == "__main__":
    classifier = DetailClassifier()

    test_texts = [
        ("집 앞 도로에 불법 주정차 차량이 많아서 통행이 어렵습니다.", "교통"),
        ("골목에 쓰레기 무단투기가 심하고 악취가 납니다.", "환경"),
        ("밤길에 가로등이 고장 나서 너무 어둡습니다.", "안전"),
        ("어디에 문의해야 할지 모르겠습니다.", "기타")
    ]

    for text, category in test_texts:
        result = classifier.classify(text, category)
        print("입력 문장:", text)
        print("대분류:", category)
        print("세부 label:", result)
        print("-" * 30)