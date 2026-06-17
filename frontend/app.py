from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


<<<<<<< Updated upstream
@app.route("/process", methods=["POST"])
def process_complaint():
    text = request.form.get("text", "")
    audio_file = request.files.get("audio")

    # 나중에 팀원 코드 연결할 부분
    # audio_file -> 음성 전처리 / STT
    # text -> Gemini API
    # 최종 민원문 생성
    # 부서 추천
=======
@app.route("/classify-image", methods=["POST"])
def classify_image():
    image_file = request.files.get("image")

    if image_file is None:
        return jsonify({
            "category": "기타"
        })

    # TODO: 이미지 분류 모델 연결
    # image_file을 전처리한 뒤 교통 / 환경 / 안전 / 기타 중 하나를 예측하도록 연결
    #
    # 예:
    # predicted_category = image_classifier.predict(image_file)
    #
    # 현재는 모델 연결 전이므로 임시값을 반환함
    predicted_category = "교통"

    return jsonify({
        "category": predicted_category
    })


@app.route("/process", methods=["POST"])
def process_complaint():
    text = request.form.get("text", "")
    image_category = request.form.get("image_category", "")
    audio_file = request.files.get("audio")

    # 나중에 팀원 코드 연결할 부분
    # image_category -> 이미지 모델이 예측한 대분류
    # audio_file -> 음성 전처리 / STT
    # text -> Gemini API 또는 민원문 재작성 AI
    # 최종 민원문 생성
    # 민원분류 및 부서 추천
>>>>>>> Stashed changes

    if text.strip():
        user_input = text.strip()
    elif audio_file:
        user_input = "업로드된 음성 파일을 바탕으로 민원 내용을 분석했습니다.\n"
    else:
        user_input = "입력된 민원 내용이 없습니다."

    final_text = f"""{user_input}"""

<<<<<<< Updated upstream
    department = "⭐추천하는 부서 출력📃"
=======
    department = "추천하는 부서 출력(연결)"
>>>>>>> Stashed changes

    return jsonify({
        "final_text": final_text,
        "department": department
    })


if __name__ == "__main__":
    app.run(debug=True)