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
7. final_text는 민원분류 AI의 학습 데이터와 비슷한 자연스러운 민원 문장 형태로 작성한다.
아래 예시처럼 문제 상황, 불편함, 요청 사항이 드러나게 작성한다.

예시:
- 집 앞 도로에 차가 계속 불법 주차되어 통행이 어렵습니다. 현장 확인 후 단속을 요청드립니다.
- 골목에 쓰레기가 며칠째 방치되어 악취가 심합니다. 빠른 수거와 주변 정리를 요청드립니다.
- 가로등이 고장 나서 밤길이 너무 어둡습니다. 안전을 위해 가로등 점검 및 수리를 요청드립니다.

단, 예시 문장을 그대로 복사하지 말고 raw_text의 내용을 바탕으로 작성한다.
final_text는 2~4문장 정도로 작성하되, 필요하면 5문장까지 작성할 수 있다.
너무 딱딱한 공문체나 제목 형식은 사용하지 않는다.
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