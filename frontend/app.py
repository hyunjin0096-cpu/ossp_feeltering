import os
import sys
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = Path(__file__).resolve().parent
REWRITER_DIR = PROJECT_ROOT / "complaint_rewriter_ai"

if str(FRONTEND_DIR) not in sys.path:
    sys.path.append(str(FRONTEND_DIR))

if str(REWRITER_DIR) not in sys.path:
    sys.path.append(str(REWRITER_DIR))

from VAD_json import start_recording, stop_recording_and_process


app = Flask(__name__)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/classify-image", methods=["POST"])
def classify_image():
    image_file = request.files.get("image")

    if image_file is None:
        return jsonify({"category": "기타"}), 400

    try:
        files = {
            "file": (
                image_file.filename,
                image_file.stream,
                image_file.mimetype,
            )
        }
        response = requests.post(
            f"{BACKEND_URL}/complaints/analyze-image",
            files=files,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

    except requests.RequestException as e:
        print("이미지 분류 API 오류:", e)
        return jsonify({
            "category": "기타",
            "error": str(e),
        }), 502

    return jsonify({
        "category": result.get("complaint_type", "기타")
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
            "error": str(e),
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
            "error": str(e),
        }), 500


@app.route("/process", methods=["POST"])
def process_complaint():
    text = request.form.get("text", "")
    image_category = request.form.get("image_category", "")
    audio_file = request.files.get("audio")

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

    try:
        response = requests.post(
            f"{BACKEND_URL}/complaints/classify",
            json={
                "text": final_text,
                "confirmed_type": image_category or "기타",
                "keywords": keywords,
            },
            timeout=30,
        )
        response.raise_for_status()
        department_data = response.json()
        department = department_data.get("recommended_department", "민원접수과")

    except requests.RequestException as e:
        print("부서 추천 API 오류:", e)
        department = "민원접수과"

    return jsonify({
        "problem": problem,
        "location": location,
        "request": request_text,
        "final_text": final_text,
        "department": department,
        "image_category": image_category,
    })


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
