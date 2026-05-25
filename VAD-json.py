import os
import sys

# 🔥ffmpeg 경로 강제 지정
try:
    import imageio_ffmpeg
    # 내장된 정상 ffmpeg 실행 파일의 경로 탐색.
    clean_ffmpeg_path = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    
    if clean_ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] = clean_ffmpeg_path + os.path.pathsep + os.environ["PATH"]
except ImportError:
    pass

# 경로 우회 완료 후 라이브러리들 로드
import wave
import threading
import numpy as np
import scipy.signal as signal
import whisper

# 1. 설정 및 상수 정의
CHUNK = 1024              
FORMAT = np.int16         
CHANNELS = 1              
RATE = 16000              
RAW_OUTPUT = "raw_input.wav"
CLEANED_OUTPUT = "cleaned_processed.wav"

VAD_THRESHOLD = 1200       
SILENCE_LIMIT = 1         

# 2. 마이크 입력 및 녹음 (VAD 및 수동 종료 포함)
def record_voice_with_vad():
    import pyaudio
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    print("\n🎤 [FEELtering] 마이크 녹음을 시작합니다. 말씀을 시작하세요...")
    print("⌨️ 녹음을 강제로 끝내려면 [Enter] 키를 누르세요!")
    
    frames = []
    silent_chunks = 0
    has_spoken = False
    
    # 엔터 키 입력을 감지하는 서브 스레드
    stop_event = threading.Event()
    def wait_for_keypress():
        input() 
        print("\n⏹️ [수동 종료] 사용자가 엔터 키를 눌러 녹음을 종료했습니다.")
        stop_event.set()

    keypress_thread = threading.Thread(target=wait_for_keypress, daemon=True)
    keypress_thread.start()
    
    while True:
        if stop_event.is_set():
            break
            
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            frames.append(data)
            
            # [오버플로우 방지] float64 형변환 적용
            audio_data_float = audio_data.astype(np.float64)
            energy = np.sqrt(np.mean(audio_data_float**2))
            
            if energy > VAD_THRESHOLD:
                if not has_spoken:
                    print("🗣️ 사용자의 발화가 감지되었습니다. (녹음 중...)")
                    has_spoken = True
                silent_chunks = 0  
            else:
                if has_spoken:
                    silent_chunks += 1
            
            # 2초간 무음 시 자동 종료
            if has_spoken and (silent_chunks > (SILENCE_LIMIT * RATE / CHUNK)):
                print("\n🤫 [자동 종료] 무음 구간이 지속되어 자동으로 녹음을 종료합니다. (무음 구간 절삭)")
                break
                
        except KeyboardInterrupt:
            print("\n⏹️ 강제 종료되었습니다.")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(RAW_OUTPUT, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"💾 원본 파일 저장 완료: {RAW_OUTPUT}")


# 3. 소음 제거 및 볼륨 정규화 (전처리)
def preprocess_audio():
    print("\n🧹 소음 제거 및 볼륨 정규화를 진행합니다...")
    
    with wave.open(RAW_OUTPUT, 'rb') as wf:
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
    
    with wave.open(CLEANED_OUTPUT, 'wb') as wf_out:
        wf_out.setparams(params)
        wf_out.writeframes(normalized_audio.tobytes())
    print(f"💾 전처리 완료 파일 저장 완료: {CLEANED_OUTPUT}")


#json형식으로 반환
def run_whisper_test():
    print("\n🤖 Whisper Base 모델을 로드하는 중입니다...")
    model = whisper.load_model("base")
    
    print("🔮 정제된 오디오 파일에서 텍스트(raw_text)를 추출 중입니다...")
    
    with wave.open(CLEANED_OUTPUT, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    
    result = model.transcribe(audio_array, fp16=False, language="ko")
    
    # ==========================================
    # ✨ [명세서 반영] 1단계 & 2단계 데이터 규격화 (JSON)
    # ==========================================
    import json
    
    # 테이블에 적힌 변수명(Key)과 데이터 타입을 그대로 매핑합니다.
    fe_sharing_data = {
        "audio_file": CLEANED_OUTPUT,      # File (.wav) 경로
        "sampling_rate": int(RATE),        # Integer (16000)
        "raw_text": str(result['text'])    # String (STT 변환 텍스트)
    }
    
    print("\n==============================================")
    print("🎉 [Hello World] 1~2주차 담당 데이터 규격화 완료")
    print("==============================================")
    # 다른 팀원들이 바로 쓸 수 있도록 JSON 형태로 예쁘게 출력
    print(json.dumps(fe_sharing_data, ensure_ascii=False, indent=2))
    print("==============================================")

    # 메인 실행 파트
if __name__ == "__main__":
    record_voice_with_vad()
    preprocess_audio()
    run_whisper_test()