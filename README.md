#  FEELtering: 생성형 AI 기반 지능형 민원 처리 파이프라인

> **시민들의 두서없고 감정적인 민원 표현을 정중한 공식 행정 서식문으로 정제하고, 멀티모달(이미지+음성) 분석과 규칙 기반 알고리즘을 융합하여 관할 처리 부서를 자동 매핑하는 AI 행정 효율화 시스템입니다.**

---

##  1. 프로젝트 주요 기능 (UI Flow)
* **[화면 1 ➔ 화면 2] 이미지 기반 1차 대분류:** 현장 사진을 업로드하면 `EfficientNet-B0` 모델이 분석하여 4대 대분류(환경, 안전, 교통, 기타)를 선제적으로 분류 및 추천합니다.
* **[화면 3] 고성능 음성 정제 및 STT:** 실시간 민원 녹음 음성의 고주파 노이즈를 필터링하고 볼륨을 정규화한 뒤, `OpenAI Whisper`를 통해 깨끗한 원문 텍스트(`raw_text`)로 변환합니다.
* **[화면 4 ➔ 화면 5] 생성형 AI 문장 정제 및 최종 부서 매핑:** `Google Gemini API`가 감정어·비속어를 필터링하여 표준 행정문으로 정제하고 맥락 키워드를 추출합니다. 이후 백엔드 컨트롤러가 **[이미지 대분류값 + Gemini 키워드]**를 조합한 **규칙 기반(Rule-based) 매퍼**를 구동하여 최종 8대 세부분류 및 관할 부서 상세 정보를 출력합니다.

---

##  2. 담당 역할 및 기술 스택

### 👥 팀원별 역할 분담
* **오현진 (팀장)**: `음성 AI & 입출력 파트` | FastAPI 백엔드 아키텍처 및 REST API 파이프라인 구축, SciPy 기반 오디오 전처리(Butterworth 필터, 볼륨 정규화) 알고리즘 구현, OpenAI Whisper 모델 연동 및 STT 엔진 최적화.
* **이예랑**: `분류 AI & 데이터 파트` | PyTorch 기반 EfficientNet-B0 이미지 분류 모델 학습(`best.pth`) 및 연동, 데이터셋 라벨링 구조화, 대분류값과 Gemini 키워드를 상호 연산하는 규칙 기반 부서 추천 매퍼(`recommend_department`) 구현 및 JSON DB 구축.
* **김지호**: `생성 AI & 프론트 파트` | Google Gemini API 기반 표준 행정 서식문 변환 프롬프트 엔지니어링, 맥락 중심 핵심 키워드(`matched_keywords`) 추출 로직 구현, 서비스 전체 UI/UX 인터페이스 및 와이어프레임 디자인.

###  기술 스택 (Tech Stack)
* **Backend**: FastAPI, Uvicorn, Pydantic
* **AI / ML**: PyTorch, OpenAI Whisper (Base), Google Gemini API, EfficientNet-B0
* **Audio / Data Processing**: SciPy, NumPy, Wave, Pillow
* **Frontend**: HTML5, CSS3, JavaScript

---

##  3. 디렉토리 구조 (Directory Structure)
```text
├── ai/
│   ├── data/
│   ├── department_recommender.py       # 규칙 기반 부서 추천 코어 알고리즘
│   └── detail_classifier.py            # 세부분류 엔진 클래스
│
├── backend/
│   └── app/
│       ├── models/
│       │   └── best.pth                # 학습 완료된 EfficientNet-B0 가중치 파일
│       ├── services/
│       │   ├── __init__.py
│       │   └── department_recommender.py
│       ├── __init__.py
│       ├── app.py
│       └── main.py                     # FastAPI 메인 엔드포인트 제어 스크립트
│
└── frontend/
    ├── static/
    │   ├── script.js                   # 마이크 녹음 데이터 Blob 변환 및 전송 프론트 로직
    │   └── style.css
    ├── templates/
    │   └── index.html
    └── VAD_json.py
```
---
## 🔌 4. 핵심 API 명세 (Core APIs)

### ① 이미지 1차 분류 엔드포인트
> **기능:** 업로드된 현장 사진을 분석하여 상위 4대 카테고리 중 하나를 예측합니다.

- **URL:** `/complaints/analyze-image`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request 파라미터:**
  
  | 파라미터명 | 타입 | 필수 여부 | 설명 |
  | :--- | :--- | :---: | :--- |
  | `file` | `UploadFile` | 필수 | 분석할 민원 현장 이미지 파일 |

- **Response 구조 (JSON):**
  ```json
  {
    "complaint_type": "환경"
  }

### ② 음성 텍스트 변환 엔드포인트
>**기능:** 실시간으로 녹음된 오디오 파일의 노이즈를 제어하고 한국어 텍스트(STT)를 추출합니다.
-**URL:** /audio/transcribe
-**Method:** POST
-**Content-Type:** multipart/form-data
-**Request 파라미터:**

 | 파라미터명 | 타입 | 필수 여부 | 설명 |
  | :--- | :--- | :---: | :--- |
  | `file` | `UploadFile` | 필수 | 녹음된 .wav 음성 파일 |

- **Response 구조 (JSON):**
  ```json
 {
  "audio_file": "temp_audio/cleaned_voice.wav",
  "sampling_rate": 16000,
  "raw_text": "여기 도로에 싱크홀 같은 구멍이 크게 파여 있어서 차들이 급정거하고 난리에요 위험하니까 빨리 조치해 주세요"
}

### ③ 민원 통합 정제 및 최종 부서 추천 엔드포인트
> **기능:** 이미지 분류 결과와 음성 텍스트를 조합하여 8대 세부분류를 확정하고 최종 관할 행정 부서 정보를 반환합니다.

- **URL:** `/complaints/classify`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Request Body (JSON):**
  ```json
  {
    "text": "여기 도로에 싱크홀 같은 구멍이 크게 파여 있어서 차들이 급정거하고 난리에요 위험하니까 빨리 조치해 주세요",
    "confirmed_type": "안전",
    "keywords": ["도로파손", "싱크홀"]
  }
---
  -**Response 구조 (JSON):**
  
  ```json
  {
  "complaint_type": "road_damage",
  "type_confidence": 1.0,
  "matched_keywords": ["도로파손", "싱크홀", "포트홀"],
  "recommended_department": "도로과 도로관리팀",
  "department_reason": "도로 파손 및 포트홀(싱크홀)로 인한 차량 안전사고 예방 관할 부서입니다.",
  "contact": "02-2199-XXXX",
  "website": "[https://www.epeople.go.kr](https://www.epeople.go.kr)",
  "required_documents": ["현장 사진 필수 첨부", "민원신청서"],
  "extra_info": "야간 및 주말 공백기 발생 시 긴급 재난 안전 상황실로 자동 즉시 핫라인 연결이 가능합니다.",
  "keywords": ["도로파손", "싱크홀"]
}
```
---

##  5. 설치 및 시작 가이드

### 1) 가상환경 구축 및 필수 패키지 설치
로컬 PC 또는 서버 환경에 맞는 패키지들을 일괄 설치합니다.

```bash
# 종속성 라이브러리 일괄 설치
pip install -r requirements.txt
```
> 📦 **주요 프레임워크 및 라이브러리 버전**
> - **핵심 서버 인프라:** `fastapi`, `uvicorn`, `pydantic`
> - **AI & 신호 처리 알고리즘:** `torch`, `torchvision`, `scipy`, `numpy`, `openai-whisper`, `google-generativeai`

### 2) 백엔드 서버 구동
Uvicorn ASGI 웹 서버를 가동하여 API 엔드포인트를 리스닝 상태로 전환합니다.

```bash
# FastAPI 애플리케이션 실행 (자동 리로드 모드)
uvicorn backend.app.main:app --reload
```
### API 개발 테스트 가이드
서버가 정상적으로 구동되면 브라우저를 열고 아래 주소로 접속하세요. 백엔드 코드와 실시간 연동되는 대화형 테스트 문서가 제공됩니다.

* **인터랙티브 API 명세서:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI)
* **대체 문서 페이지:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) (ReDoc)
