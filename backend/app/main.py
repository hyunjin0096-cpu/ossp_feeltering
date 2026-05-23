from fastapi import FastAPI
from pydantic import BaseModel
from app.services.complaint_classifier import classify_complaint
from app.services.department_recommender import recommend_department

app = FastAPI()


class ComplaintRequest(BaseModel):
    text: str
    keywords: list[str] = []


@app.post("/complaints/classify")
def classify_and_recommend(request: ComplaintRequest):
    classification_result = classify_complaint(request.text)

    complaint_type = classification_result["complaint_type"]
    department_result = recommend_department(complaint_type)

    return {
        "complaint_type": complaint_type,
        "type_confidence": classification_result["type_confidence"],
        "matched_keywords": classification_result.get("matched_keywords", []),
        "recommended_department": department_result["recommended_department"],
        "department_reason": department_result["department_reason"],
        "contact": department_result["contact"],
        "website": department_result["website"],
        "required_documents": department_result["required_documents"],
        "extra_info": department_result["extra_info"],
        "keywords": request.keywords
    }