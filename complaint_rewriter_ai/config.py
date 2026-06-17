import os
from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")