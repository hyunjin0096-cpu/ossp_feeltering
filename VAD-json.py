import os
import io
import wave
import shutil
import numpy as np
import scipy.signal as signal
import whisper
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

# 🔥ffmpeg 경로 강제 지정
try:
    import imageio_ffmpeg
    clean_ffmpeg_path = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if clean_ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] = clean_ffmpeg_path + os.path.pathsep + os.environ["PATH"]
except ImportError:
    pass

router = APIRouter(prefix="/audio", tags=["Audio STT"])

# 1. 설정 및 상수 정의
RATE = 16000
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

print("\n🤖 Whisper Base 모델을 로드하는 중입니다...")
whisper_model = whisper.load_model("base")


# 3. 소음 제거 및 볼륨 정규화 (전처리)
def preprocess_audio(raw_file_path: str, cleaned_file_path: str):
    with wave.open(raw_file_path, 'rb') as wf:
        params = wf.getparams()
        n_frames = wf.getnframes()
        audio_bytes = wf.readframes(n_frames)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    
    nyquist = 0.5 * RATE
    cutoff = 4000.0
    normal_cutoff = cutoff / nyquist
    b, a = signal.butter(5, normal_cutoff, btype='low', analog=False)
    filtered_audio = signal.lfilter(b, a, audio_data)
    
    max_val = np.max(np.abs(filtered_audio))
    if max_val > 0:
        normalized_audio = (filtered_audio / max_val) * 26000  
    else:
        normalized_audio = filtered_audio
        
    normalized_audio = normalized_audio.astype(np.int16)
    
    with wave.open(cleaned_file_path, 'wb') as wf_out:
        wf_out.setparams(params)
        wf_out.writeframes(normalized_audio.tobytes())


# json형식으로 반환
@router.post("/transcribe")
async def run_whisper_test(file: UploadFile = File(...)):
    raw_path = os.path.join(TEMP_DIR, f"raw_{file.filename}")
    cleaned_path = os.path.join(TEMP_DIR, f"cleaned_{file.filename}")
    
    try:
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        preprocess_audio(raw_path, cleaned_path)
        
        print(" 정제된 오디오 파일에서 텍스트를 추출 중입니다...")
        with wave.open(cleaned_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        result = whisper_model.transcribe(audio_array, fp16=False, language="ko")
        
        # ==========================================
        # ✨ [명세서 반영] 1단계 & 2단계 데이터 규격화 (JSON)
        # ==========================================
        # 테이블에 적힌 변수명(Key)과 데이터 타입을 그대로 매핑합니다.
        fe_sharing_data = {
            "audio_file": cleaned_path,      # File (.wav) 경로
            "sampling_rate": int(RATE),        # Integer (16000)
            "raw_text": str(result['text'])    # String (STT 변환 텍스트)
        }
        
        return fe_sharing_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
