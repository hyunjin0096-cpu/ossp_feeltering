import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from VAD_json import start_recording, stop_recording_and_process

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REWRITER_DIR = PROJECT_ROOT / "complaint_rewriter_ai"

if str(REWRITER_DIR) not in sys.path:
    sys.path.append(str(REWRITER_DIR))

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/classify-image", methods=["POST"])
def classify_image():
    image_file = request.files.get("image")

    if image_file is None:
        return jsonify({
            "category": "기타"
        })

    # TODO: 이미지 분류 모델 연결
    predicted_category = "교통"

    return jsonify({
        "category": predicted_category
    })


@app.route("/start-recording", methods=["POST"])
def start_recording_route():
    try:
        result = start_recording()
        return jsonify(result)

    except Exception as e:
        print("녹음 시작 오류:", e)

        return jsonify({
            "success": False,
            "message": "녹음 시작 중 서버 오류가 발생했습니다.",
            "error": str(e)
        }), 500


@app.route("/stop-recording", methods=["POST"])
def stop_recording_route():
    try:
        result = stop_recording_and_process()
        return jsonify(result)

    except Exception as e:
        print("녹음 처리 오류:", e)

        return jsonify({
            "success": False,
            "message": "녹음 처리 중 서버 오류가 발생했습니다.",
            "error": str(e)
        }), 500


@app.route("/process", methods=["POST"])
def process_complaint():
    text = request.form.get("text", "")
    image_category = request.form.get("image_category", "")
    audio_file = request.files.get("audio")

    # image_category -> 이미지 모델이 예측한 대분류
    # audio_file -> 파일 업로드 방식 사용할 경우 연결
    # text -> 직접 입력 또는 VAD STT 결과가 들어온 텍스트

    if text.strip():
        user_input = text.strip()
    elif audio_file:
        user_input = "업로드된 음성 파일을 바탕으로 민원 내용을 분석했습니다.\n"
    else:
        user_input = "입력된 민원 내용이 없습니다."

    from complaint_rewriter import rewrite_complaint

    rewritten = rewrite_complaint(user_input)
    keywords = rewritten.get("keywords", ["정보 없음", "정보 없음", "정보 없음"])
    final_text = rewritten.get("text", user_input)

    problem = keywords[0] if len(keywords) > 0 else "정보 없음"
    location = keywords[1] if len(keywords) > 1 else "정보 없음"
    request_text = keywords[2] if len(keywords) > 2 else "정보 없음"

    department = "⭐추천하는 부서 출력📃"

    return jsonify({
        "problem": problem,
        "location": location,
        "request": request_text,
        "final_text": final_text,
        "department": department,
        "image_category": image_category
    })


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
