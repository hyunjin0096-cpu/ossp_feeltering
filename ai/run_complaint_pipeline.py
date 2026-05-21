from predict_category import CategoryClassifier
from detail_classifier import DetailClassifier
from department_recommender import DepartmentRecommender


class ComplaintPipeline:
    def __init__(self):
        self.category_classifier = CategoryClassifier()
        self.detail_classifier = DetailClassifier()
        self.department_recommender = DepartmentRecommender()

    def analyze(self, text: str) -> dict:
        # 1차 AI 대분류
        category = self.category_classifier.predict(text)

        # 2차 규칙 기반 세부 분류
        detail_label = self.detail_classifier.classify(text, category)

        # 3차 부서 추천
        department_info = self.department_recommender.recommend(detail_label)

        return {
            "input_text": text,
            "category": category,
            "detail_label": detail_label,
            "department": department_info.get("department"),
            "reason": department_info.get("reason"),
            "contact": department_info.get("contact"),
            "website": department_info.get("website"),
            "required_documents": department_info.get("required_documents"),
            "extra_info": department_info.get("extra_info")
        }


if __name__ == "__main__":
    pipeline = ComplaintPipeline()

    text = input("민원 문장을 입력하세요: ")
    result = pipeline.analyze(text)

    print("\n===== 민원 분석 결과 =====")
    print("입력 문장:", result["input_text"])
    print("1차 대분류:", result["category"])
    print("세부 label:", result["detail_label"])
    print("추천 부서:", result["department"])
    print("추천 이유:", result["reason"])
    print("연락처:", result["contact"])
    print("사이트:", result["website"])
    print("준비 서류:", result["required_documents"])
    print("추가 안내:", result["extra_info"])