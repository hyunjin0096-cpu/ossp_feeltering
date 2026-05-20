from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process_complaint():
    text = request.form.get("text", "")
    audio_file = request.files.get("audio")

    # 나중에 팀원 코드 연결할 부분
    # audio_file -> 음성 전처리 / STT
    # text -> Gemini API
    # 최종 민원문 생성
    # 부서 추천

    if text.strip():
        user_input = text.strip()
    elif audio_file:
        user_input = "업로드된 음성 파일을 바탕으로 민원 내용을 분석했습니다.\n"
    else:
        user_input = "입력된 민원 내용이 없습니다."

    final_text = f"""{user_input}"""

    department = "⭐추천하는 부서 출력📃"

    return jsonify({
        "final_text": final_text,
        "department": department
    })


if __name__ == "__main__":
    app.run(debug=True)