from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import shutil
import os
from ultralytics import YOLO

from app.services.complaint_classifier import classify_complaint
from app.services.department_recommender import recommend_department

app = FastAPI()

YOLO_MODEL_PATH = "app/models/best.pt" 
yolo_model = YOLO(YOLO_MODEL_PATH) if os.path.exists(YOLO_MODEL_PATH) else None


# [화면 1 -> 화면 2] 호출 : YOLO 이미지 분석 후 4대 대분류값 반환
@app.post("/complaints/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not yolo_model:
        return {"complaint_type": "교통"}

    try:
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        results = yolo_model(temp_file_path, conf=0.25)
        
        yolo_label = "general_complaint" 
        if len(results) > 0 and len(results[0].boxes) > 0:
            class_id = int(results[0].boxes[0].cls[0].item())
            yolo_label = yolo_model.names[class_id]

        os.remove(temp_file_path)

        yolo_to_main_category = {
            "illegal_parking": "교통",
            "road_damage": "교통",
            "waste_cleaning": "환경",
            "noise": "환경",
            "sewer_drainage": "환경",
            "illegal_advertisement": "환경",
            "streetlight": "안전",
            "general_complaint": "기타"
        }
        
        main_category = yolo_to_main_category.get(yolo_label, "기타")

        return {
            "complaint_type": main_category 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 데이터 모델 수정
class ComplaintRequest(BaseModel):
    text: str                       # Whisper 변환 텍스트
    confirmed_type: str             # 화면 2에서 유저가 확정한 대분류값 ("교통", "환경", "안전", "기타")
    keywords: List[str] = []        # 추가 키워드


# [화면 3 -> 화면 5] 호출 : 제미나이 텍스트 정제 및 기존 규칙 기반 코드 데이터 연결
@app.post("/complaints/classify")
def classify_and_recommend(request: ComplaintRequest):
    
    classification_result = classify_complaint(request.text)

    sub_category_key = classification_result.get("complaint_type", "etc")
    department_result = recommend_department(sub_category_key)

    return {
        "complaint_type": sub_category_key,  # 8대 세부분류 영문 Key
        "type_confidence": classification_result.get("type_confidence", 1.0),
        "matched_keywords": classification_result.get("matched_keywords", []),
        "recommended_department": department_result["recommended_department"],
        "department_reason": department_result["department_reason"],
        "contact": department_result["contact"],
        "website": department_result["website"],
        "required_documents": department_result["required_documents"],
        "extra_info": department_result["extra_info"],
        "keywords": request.keywords  
    }
