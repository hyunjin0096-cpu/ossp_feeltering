from pathlib import Path
from typing import List
import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

try:
    import torch
    import torch.nn as nn
    from PIL import Image
    from torchvision import models, transforms
except ModuleNotFoundError:
    torch = None
    nn = None
    Image = None
    models = None
    transforms = None

from ai.detail_classifier import DetailClassifier
from backend.app.services.department_recommender import recommend_department


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATHS = [
    BASE_DIR / "models" / "best.pth",
    BASE_DIR.parent / "models" / "best.pth",
    Path.cwd() / "backend" / "app" / "models" / "best.pth",
    Path.cwd() / "app" / "models" / "best.pth",
]

device = torch.device("cuda" if torch and torch.cuda.is_available() else "cpu") if torch else None
efficientnet_model = None
img_transforms = None
detail_classifier = DetailClassifier()

if torch and nn and models and transforms:
    model_path = next((path for path in MODEL_PATHS if path.exists()), None)
    img_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    if model_path:
        efficientnet_model = models.efficientnet_b0(weights=None)
        num_ftrs = efficientnet_model.classifier[1].in_features
        efficientnet_model.classifier[1] = nn.Linear(num_ftrs, 3)
        efficientnet_model.load_state_dict(torch.load(model_path, map_location=device))
        efficientnet_model.to(device)
        efficientnet_model.eval()


@app.post("/complaints/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not efficientnet_model or not Image or not img_transforms:
        return {"complaint_type": "교통"}

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        input_tensor = img_transforms(image).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = efficientnet_model(input_tensor)
            _, preds = torch.max(outputs, 1)
            class_id = preds.item()

        class_to_main_category = {
            0: "환경",
            1: "안전",
            2: "교통",
        }
        return {"complaint_type": class_to_main_category.get(class_id, "기타")}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class ComplaintRequest(BaseModel):
    text: str
    confirmed_type: str
    keywords: List[str] = []


@app.post("/complaints/classify")
def classify_and_recommend(request: ComplaintRequest):
    detail_label = detail_classifier.classify(
        text=request.text,
        category=request.confirmed_type or "기타",
    )
    department_result = recommend_department(detail_label)

    return {
        "complaint_type": detail_label,
        "type_confidence": 1.0,
        "matched_keywords": request.keywords,
        "recommended_department": department_result.get("department", "민원접수과"),
        "department_reason": department_result.get("reason", "일반 민원입니다."),
        "contact": department_result.get("contact", "02-2199-6114"),
        "website": department_result.get("website", "https://www.epeople.go.kr"),
        "required_documents": department_result.get("required_documents", []),
        "extra_info": department_result.get("extra_info", ""),
        "keywords": request.keywords,
    }
