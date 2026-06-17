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


# [화면 1 -> 화면 2] 이동 시 호출 : YOLO 이미지분석 후 4대 대분류값 반환
@app.post("/complaints/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not yolo_model:
        # 모델 파일이 없을 때 프론트 테스트 예외처리
        return {"complaint_type": "교통"}

    try:
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        results = yolo_model(temp_file_path, conf=0.25)
        
        yolo_label = "general_complaint" # 디폴트값
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
            "complaint_type": main_category # 화면 2에서 사용자에게 "00 유형이 맞습니까?" 물어볼 값
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# [화면 3 -> 화면 5] 이동 시 호출 : 세부분류값 및 정제민원문 출력
class FinalComplaintRequest(BaseModel):
    text: str                       # Whisper가 텍스트로 변환한 유저 음성 원문
    keywords: List[str] = []        # 추가로 넘겨줄 키워드 리스트


@app.post("/complaints/final-submit")
def final_submit(request: FinalComplaintRequest):
    classification_result = classify_complaint(request.text)

    sub_category_key = classification_result.get("complaint_type", "etc")

    department_result = recommend_department(sub_category_key)

    return {
        "matched_keywords": classification_result.get("matched_keywords", request.keywords),
        
        "refined_text": classification_result.get("refined_text", request.text),
        
        "recommended_department": {
            "department": department_result["recommended_department"], # 부서명
            "reason": department_result["department_reason"],         # 추천 사유
            "contact": department_result["contact"],                   # 전화번호
            "website": department_result["website"],                   # 홈페이지
            "required_documents": department_result["required_documents"], # 필요 서류
            "extra_info": department_result["extra_info"]              # 참고 사항
        }
    }
