import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
import json
import os


# =========================
# 1. 경로 설정
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "category_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models", "complaint_classifier", "model")
LABEL_MAP_PATH = os.path.join(BASE_DIR, "models", "complaint_classifier", "label_map.json")


# =========================
# 2. 데이터 불러오기
# =========================

df = pd.read_csv(DATA_PATH)

# category_dataset.csv에는 반드시 text, category 컬럼이 있어야 함
# text: 사용자 민원 문장
# category: 1차 대분류 결과, 예: 교통 / 환경 / 안전 / 기타

print("데이터 개수:", len(df))
print("컬럼 목록:", df.columns.tolist())
print("카테고리 종류:", df["category"].unique())


# =========================
# 3. 카테고리 숫자 변환
# =========================

categories = sorted(df["category"].unique())

category2id = {category: idx for idx, category in enumerate(categories)}
id2category = {idx: category for category, idx in category2id.items()}

df["category_id"] = df["category"].map(category2id)

print("category2id:", category2id)
print("id2category:", id2category)


# =========================
# 4. 학습 / 검증 데이터 분리
# =========================

train_df, valid_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["category_id"]
)

train_dataset = Dataset.from_pandas(train_df)
valid_dataset = Dataset.from_pandas(valid_df)


# =========================
# 5. 모델과 토크나이저 불러오기
# =========================

model_name = "klue/roberta-small"

tokenizer = AutoTokenizer.from_pretrained(model_name)


def tokenize(batch):
    return tokenizer(
        batch["text"],
        padding="max_length",
        truncation=True,
        max_length=128
    )


train_dataset = train_dataset.map(tokenize, batched=True)
valid_dataset = valid_dataset.map(tokenize, batched=True)

# Trainer가 정답 컬럼을 labels라는 이름으로 인식하므로 category_id를 labels로 변경
train_dataset = train_dataset.rename_column("category_id", "labels")
valid_dataset = valid_dataset.rename_column("category_id", "labels")

train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
valid_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])


# =========================
# 6. 1차 대분류 모델 생성
# =========================

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(categories),
    id2label=id2category,
    label2id=category2id
)


# =========================
# 7. 평가 지표 설정
# =========================

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro")
    }


# =========================
# 8. 학습 설정
# =========================

training_args = TrainingArguments(
    output_dir=MODEL_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir=os.path.join(BASE_DIR, "train", "logs"),
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro"
)


# =========================
# 9. Trainer 생성
# =========================

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset,
    processing_class=tokenizer,
    compute_metrics=compute_metrics
)


# =========================
# 10. 모델 학습
# =========================

trainer.train()

eval_result = trainer.evaluate()

print("최종 평가 결과:")
print(eval_result)

predictions = trainer.predict(valid_dataset)

pred_labels = np.argmax(predictions.predictions, axis=-1)
true_labels = predictions.label_ids

target_names = [id2category[i] for i in range(len(id2category))]

print("분류 성능 상세 결과:")
print(classification_report(true_labels, pred_labels, target_names=target_names))

# =========================
# 11. 모델과 토크나이저 저장
# =========================

trainer.save_model(MODEL_DIR)
tokenizer.save_pretrained(MODEL_DIR)


# =========================
# 12. 카테고리 맵 저장
# =========================

os.makedirs(os.path.dirname(LABEL_MAP_PATH), exist_ok=True)

with open(LABEL_MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(
        {
            "category2id": category2id,
            "id2category": {str(k): v for k, v in id2category.items()}
        },
        f,
        ensure_ascii=False,
        indent=2
    )


print("1차 AI 대분류 모델 학습 및 저장 완료")
