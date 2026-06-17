from ai.department_recommender import DepartmentRecommender


_recommender = DepartmentRecommender()


def recommend_department(detail_label: str) -> dict:
    department_info = _recommender.recommend(detail_label) or {}

    return {
        "sub_category_key": detail_label,
        "department": department_info.get("department", "민원접수과"),
        "reason": department_info.get("reason", "일반 민원으로 접수 후 담당 부서 배정이 필요합니다."),
        "contact": department_info.get("contact", "02-2199-6114"),
        "website": department_info.get("website", "https://www.epeople.go.kr"),
        "required_documents": department_info.get("required_documents", []),
        "extra_info": department_info.get("extra_info", ""),
    }
