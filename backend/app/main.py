from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import shutil
import os
from ultralytics import YOLO

from app.services.complaint_classifier import classify_complaint
from app.services.department_recommender import recommend_department

app = FastAPI()

# YOLO 모델 로드
YOLO_MODEL_PATH = "모델 파일 경로" 

if os.path.exists(YOLO_MODEL_PATH):
    yolo_model = YOLO(YOLO_MODEL_PATH)
else:
    # pt없이 실행 가능하도록 예외 처리
    yolo_model = None 


# [화면 1 -> 화면 2] 이미지 업로드 및 YOLO 분석 API
@app.post("/complaints/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not yolo_model:
        return {"complaint_type": "교통", "detected_object": "road_damage", "message": "YOLO 모델 파일이 없어 테스트 데이터로 반환합니다."}

    try:
        # 임시 이미지 파일 저장
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # YOLO 추론 
        results = yolo_model(temp_file_path, conf=0.25)
        
        detected_object = "general_complaint" 
        if len(results) > 0 and len(results[0].boxes) > 0:
            class_id = int(results[0].boxes[0].cls[0].item())
            detected_object = yolo_model.names[class_id]

        
        os.remove(temp_file_path)

        # 규칙 기반 영어-한글 대분류 매핑
        mapping = {
            "illegal_parking": "교통",
            "road_damage": "교통",
            "waste_cleaning": "환경",
            "noise": "환경",
            "sewer_drainage": "환경",
            "illegal_advertisement": "환경",
            "streetlight": "안전",
            "general_complaint": "기타"
        }
        mapped_category = mapping.get(detected_object, "기타")

        return {
            "complaint_type": mapped_category,
            "detected_object": detected_object
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# [화면 3 -> 화면 5] 음성 텍스트 취합 및 최종 결과 출력 API
class FinalComplaintRequest(BaseModel):
    text: str                       # Whisper가 텍스트로 변환한 유저 음성 내용
    confirmed_type: str             # 화면 2에서 유저를 거친 대분류
    keywords: List[str] = []        # YOLO가 찾았던 객체명 리스트


@app.post("/complaints/final-submit")
def final_submit(request: FinalComplaintRequest):
    
    # 유저가 확정한 분류명을 힌트로 주어 Gemini(classify_complaint) 호출
    prompt_input = f"[확정 유형: {request.confirmed_type}] {request.text}"
    classification_result = classify_complaint(prompt_input)

    # Gemini 결과에서 타입을 가져오고, 없으면 유저가 확정한 타입 사용
    complaint_type = classification_result.get("complaint_type", request.confirmed_type)
    department_result = recommend_department(complaint_type)

    return {
        "complaint_type": complaint_type,
        "type_confidence": classification_result.get("type_confidence", 1.0),
        "matched_keywords": classification_result.get("matched_keywords", request.keywords),
        "recommended_department": department_result["recommended_department"],
        "department_reason": department_result["department_reason"],
        "contact": department_result["contact"],
        "website": department_result["website"],
        "required_documents": department_result["required_documents"],
        "extra_info": department_result["extra_info"],
        "keywords": request.keywords
    }
