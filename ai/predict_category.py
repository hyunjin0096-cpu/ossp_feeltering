import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_DIR = "./models/complaint_classifier/model"
LABEL_MAP_PATH = "./models/complaint_classifier/label_map.json"


class CategoryClassifier:
    def __init__(self):
        # label_map.json 불러오기
        with open(LABEL_MAP_PATH, "r", encoding="utf-8") as f:
            label_data = json.load(f)

        # 저장 방식에 따라 key 이름이 다를 수 있어서 둘 다 대응
        self.id2category = label_data.get("id2category")

        if self.id2category is None:
            raise ValueError("label_map.json 안에 id2category가 없습니다.")

        # JSON은 key가 문자열로 저장되므로 int 변환
        self.id2category = {int(k): v for k, v in self.id2category.items()}

        # 저장된 tokenizer와 model 불러오기
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

        # 예측 모드
        self.model.eval()

    def predict(self, text: str) -> str:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            predicted_id = torch.argmax(logits, dim=1).item()

        predicted_category = self.id2category[predicted_id]
        return predicted_category


if __name__ == "__main__":
    classifier = CategoryClassifier()

    text = input("민원 문장을 입력하세요: ")
    result = classifier.predict(text)

    print("예측 대분류:", result)