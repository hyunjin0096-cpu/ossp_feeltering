from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import io
import os
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

# 🔗 기존 서비스 함수들 (이예랑 학우님 매핑 파일 포함)
from app.services.complaint_classifier import classify_complaint
from app.services.department_recommender import recommend_department

app = FastAPI()

# ⚙️ EfficientNet-B0 모델 로드 및 전처리 설정 (YOLO 완전 대체)
MODEL_PATH = "app/models/best.pth"  # 팀원이 학습시킨 EfficientNet-B0 파일명 반영
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if os.path.exists(MODEL_PATH):
    # EfficientNet-B0 구조 선언
    efficientnet_model = models.efficientnet_b0(weights=None)
    # 최종 출력 클래스 개수 설정 (0, 1, 2 대응을 위해 3개 레이어로 설정)
    num_ftrs = efficientnet_model.classifier[1].in_features
    efficientnet_model.classifier[1] = nn.Linear(num_ftrs, 3) 
    
    # best.pth 가중치 파일 로드
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
        # 모델 파일이 없을 때 프론트엔드 연동 테스트를 위한 예외 처리 (디폴트값)
        return {"complaint_type": "교통"}

    try:
        # 1. 파일 읽기 및 이미지 객체 변환
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. 이미지 전처리 및 디바이스(CPU/GPU) 할당
        input_tensor = img_transforms(image).unsqueeze(0).to(device)

        # 3. 모델 추론
        with torch.no_grad():
            outputs = efficientnet_model(input_tensor)
            _, preds = torch.max(outputs, 1)
            class_id = preds.item()

        # 4. 라벨링 매핑 적용 -> {'environment': 0, 'safety': 1, 'traffic': 2}
        class_to_main_category = {
            0: "환경",  # environment
            1: "안전",  # safety
            2: "교통"   # traffic
        }
        
        # 매핑에 없는 인덱스는 '기타'로 처리
        main_category = class_to_main_category.get(class_id, "기타")

        return {
            "complaint_type": main_category # 화면 2에서 사용자에게 "OO 유형이 맞습니까?" 물어볼 값
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2. Request 데이터 모델 ---
class ComplaintRequest(BaseModel):
    text: str                       # Whisper 변환 텍스트
    confirmed_type: str             # 화면 2에서 유저가 확정한 대분류 ("교통", "환경", "안전", "기타")
    keywords: List[str] = []        # 추가 키워드 리스트


# [화면 3 -> 화면 5] 호출 : 제미나이 분류 결과값 ➔ 규칙 기반 함수(recommend_department)로 바로 토스!
@app.post("/complaints/classify")
def classify_and_recommend(request: ComplaintRequest):
    # 1. 제미나이가 문맥을 분석하여 8대 세부분류 영문 Key를 결정합니다.
    classification_result = classify_complaint(request.text)

    # 2. 제미나이가 내뱉은 영문 Key(예: 'road_damage')를 가져옵니다.
    sub_category_key = classification_result.get("complaint_type", "etc")
    
    # 3. 이 Key를 규칙 기반 데이터 매퍼(recommend_department)에 그대로 던집니다.
    department_result = recommend_department(sub_category_key)

    # 4. 기존 프론트엔드 리턴 구조 100% 동일하게 유지하여 반환
    return {
        "complaint_type": sub_category_key,  
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
