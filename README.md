# feeltering project
# 🎙️ Voice AI & Input/Output

본 브랜치는 오디오 음성 입력 수신, 무음 구간 감지(VAD)를 통한 잡음 제거, 그리고 Whisper STT 모델을 활용한 텍스트 변환(raw_text 추출) 단계를 담당합니다. 팀 데이터 명세서 규격에 맞추어 다음 단계로 전달할 데이터 패키징(JSON)까지 구현이 완료되었습니다.

---

## 🛠️ 개발 기능 요약
1. **음성 녹음 및 VAD (Voice Activity Detection)**
   - 마이크 입력을 실시간으로 수신하여 가청 음성 구간을 감지합니다.
   - 주변 화이트 노이즈 및 침묵 구간을 자동으로 필터링하여 정제된 데이터만 추출합니다.
2. **Whisper STT 텍스트 변환**
   - OpenAI의 Whisper Base 모델을 연동하여 정제된 오디오를 한국어 텍스트(`raw_text`)로 정확하게 변환합니다.
   - Windows 환경 내 `ffmpeg` 바이너리 충돌 문제를 완전히 우회하도록 넘파이 배열(Numpy array) 기반의 인메모리 파이프라인으로 설계하여 안정성을 극대화했습니다.
3. **데이터 규격화 (JSON 출력)**
   - 팀 협업 명세서의 데이터 타입 및 Key 규격을 완벽히 준수하여 최종 데이터를 출력합니다.

---

## 📋 데이터 매핑 정보 (1~2단계 완료)

| 단계 | 변수명 (Key) | 데이터 타입 | 담당자 | 설명 |
| :--- | :--- | :--- | :--- | :--- |
| **1. 음성 입력** | `audio_file` | File (.wav) | **현진** | 정제 완료된 파일 경로 |
| | `sampling_rate` | Integer | **현진** | 오디오 샘플링 주파수 (16000Hz) |
| **2. 텍스트 변환**| `raw_text` | String | **지호** | STT 모델이 변환한 순수 텍스트 |

---

## 🚀 실행 방법

### 1. 필수 패키지 설치
원활한 오디오 처리 및 Whisper 구동을 위해 다음 라이브러리 설치가 필요합니다.
```bash
pip install numpy scipy openai-whisper ffmpeg-python imageio-ffmpeg
