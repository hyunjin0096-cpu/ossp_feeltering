from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import io
import os
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from app.services.complaint_classifier import classify_complaint
from app.services.department_recommender import recommend_department

app = FastAPI()

# ⚙️ EfficientNet-B0 모델 로드 및 전처리 설정
MODEL_PATH = "app/models/best.pth"  
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if os.path.exists(MODEL_PATH):
    efficientnet_model = models.efficientnet_b0(weights=None)
    num_ftrs = efficientnet_model.classifier[1].in_features
    efficientnet_model.classifier[1] = nn.Linear(num_ftrs, 3) 
    
    efficientnet_model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    efficientnet_model.to(device)
    efficientnet_model.eval()
else:
    efficientnet_model = None

# EfficientNet 표준 이미지 전처리 파이프라인
img_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


# [화면 1 -> 화면 2] 호출 : EfficientNet-B0 이미지 분석 후 한글 4대 대분류 반환
@app.post("/complaints/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not efficientnet_model:
        return {"complaint_type": "교통"}

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        input_tensor = img_transforms(image).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = efficientnet_model(input_tensor)
            _, preds = torch.max(outputs, 1)
            class_id = preds.item()

        # 라벨링 매핑 -> {'environment': 0, 'safety': 1, 'traffic': 2}
        class_to_main_category = {
            0: "환경",
            1: "안전",
            2: "교통"
        }
        
        main_category = class_to_main_category.get(class_id, "기타")
        return {"complaint_type": main_category}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Request 데이터 모델 ---
class ComplaintRequest(BaseModel):
    text: str                       # Whisper 변환 텍스트 원문
    confirmed_type: str             # 화면 2에서 유저가 확정한 대분류 ("교통", "환경", "안전", "기타")
    keywords: List[str] = []        # 추가 키워드 리스트


# [화면 3 -> 화면 5] 호출 : 대분류값과 제미나이 키워드를 규칙 기반 코드의 입력값으로 통합 연동
@app.post("/complaints/classify")
def classify_and_recommend(request: ComplaintRequest):
    # 1. 제미나이 가동: 오직 문장 정제 및 핵심 키워드(matched_keywords) 추출만 담당
    classification_result = classify_complaint(request.text)
    extracted_keywords = classification_result.get("matched_keywords", [])

    department_result = recommend_department(
        main_category=request.confirmed_type, 
        keywords=extracted_keywords
    )

    # 3. 기존 프론트엔드가 쓰던 리턴 Key 구조 100% 동일하게 맞춰서 최종 반환
    return {
        "complaint_type": department_result.get("sub_category_key", "etc"),  # 규칙 기반 코드가 최종 도출한 8대 세부분류 영문 Key
        "type_confidence": classification_result.get("type_confidence", 1.0),
        "matched_keywords": extracted_keywords,
        "recommended_department": department_result.get("department", "민원접수팀"),
        "department_reason": department_result.get("reason", "일반 민원입니다."),
        "contact": department_result.get("contact", "02-2199-6114"),
        "website": department_result.get("website", "https://www.epeople.go.kr"),
        "required_documents": department_result.get("required_documents", []),
        "extra_info": department_result.get("extra_info", ""),
        "keywords": request.keywords  
    }
