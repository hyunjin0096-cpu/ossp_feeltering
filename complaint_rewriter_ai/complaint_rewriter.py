import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


def rewrite_complaint(raw_text: str) -> dict:
    """
    STT가 변환한 텍스트(raw_text)를 받아서
    1. 문제 상황, 장소, 요청 사항을 추출하고
    2. 공공기관 제출용 최종 민원문으로 재구성한 뒤
    keywords와 text 형태로 반환한다.

    반환 형식:
    {
        "keywords": ["문제 상황", "장소", "요청 사항"],
        "text": "최종 민원문"
    }
    """

    if not raw_text or not raw_text.strip():
        return {
            "keywords": ["정보 없음", "정보 없음", "정보 없음"],
            "text": ""
        }

    prompt = f"""
너는 STT 모델이 변환한 민원 텍스트를 공공기관 제출용 민원문으로 재작성하고,
핵심 키워드를 추출하는 백엔드 AI 모듈이다.

아래 raw_text를 분석해서 반드시 JSON 형식으로만 답해라.

역할:
1. STT 변환 과정에서 생긴 어색한 표현이나 오타를 자연스럽게 보정한다.
2. 문제 상황, 장소, 요청 사항을 각각 추출한다.
3. 사용자의 민원 내용을 공공기관에 제출할 수 있는 정중하고 명확한 최종 민원문으로 재구성한다.

중요 조건:
1. 사용자가 말하지 않은 구체적인 주소, 날짜, 기관명, 사건 내용은 임의로 만들지 않는다.
2. 사용자가 말한 핵심 단어는 가능한 한 유지한다.
   예: 불법 주정차, 쓰레기, 악취, 도로 파손, 가로등, 소음, 무단투기, 단속, 수거, 보수
3. 뒤의 민원 유형 분류 AI가 키워드를 찾을 수 있도록 final_text에는 문제 상황을 구체적으로 표현한다.
4. problem은 구체적인 문제 상황만 작성한다.
5. location은 민원 발생 위치만 작성한다.
6. request는 사용자가 원하는 조치 사항만 작성한다.
7. final_text는 공공기관 제출용 민원문 형태로 정중하게 작성한다.
8. 정보가 없으면 "정보 없음"이라고 작성한다.
9. JSON 이외의 설명 문장은 절대 쓰지 않는다.

raw_text:
{raw_text}

출력 형식:
{{
  "problem": "",
  "location": "",
  "request": "",
  "final_text": ""
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json")
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "keywords": ["정보 없음", "정보 없음", "정보 없음"],
            "text": raw_text
        }

    problem = result.get("problem", "정보 없음")
    location = result.get("location", "정보 없음")
    request = result.get("request", "정보 없음")
    final_text = result.get("final_text", raw_text)

    return {
        "keywords": [problem, location, request],
        "text": final_text
    }