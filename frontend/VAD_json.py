import os
import sys
import wave
import threading
import json

# ffmpeg 경로 강제 지정
try:
    import imageio_ffmpeg

    clean_ffmpeg_path = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

    if clean_ffmpeg_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = clean_ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    pass

# 경로 우회 완료 후 라이브러리들 로드
import numpy as np
import scipy.signal as signal
import whisper


# =========================
# 1. 설정 및 상수 정의
# =========================

CHUNK = 1024
FORMAT = np.int16
CHANNELS = 1
RATE = 16000

RAW_OUTPUT = "raw_input.wav"
CLEANED_OUTPUT = "cleaned_processed.wav"

VAD_THRESHOLD = 1200
SILENCE_LIMIT = 1

_whisper_model = None


# =========================
# 2. 기존 터미널 실행용 녹음 함수
# =========================

def record_voice_with_vad():
    import pyaudio

    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("\n🎤 [FEELtering] 마이크 녹음을 시작합니다. 말씀을 시작하세요...")
    print("⌨️ 녹음을 강제로 끝내려면 [Enter] 키를 누르세요!")

    frames = []
    silent_chunks = 0
    has_spoken = False

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

            audio_data_float = audio_data.astype(np.float64)
            energy = np.sqrt(np.mean(audio_data_float ** 2))

            if energy > VAD_THRESHOLD:
                if not has_spoken:
                    print("🗣️ 사용자의 발화가 감지되었습니다. (녹음 중...)")
                    has_spoken = True
                silent_chunks = 0
            else:
                if has_spoken:
                    silent_chunks += 1

            if has_spoken and (silent_chunks > (SILENCE_LIMIT * RATE / CHUNK)):
                print("\n🤫 [자동 종료] 무음 구간이 지속되어 자동으로 녹음을 종료합니다.")
                break

        except KeyboardInterrupt:
            print("\n⏹️ 강제 종료되었습니다.")
            break

    sample_width = p.get_sample_size(pyaudio.paInt16)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(RAW_OUTPUT, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"💾 원본 파일 저장 완료: {RAW_OUTPUT}")


# =========================
# 3. 소음 제거 및 볼륨 정규화
# =========================

def preprocess_audio():
    print("\n🧹 소음 제거 및 볼륨 정규화를 진행합니다...")

    with wave.open(RAW_OUTPUT, "rb") as wf:
        params = wf.getparams()
        n_frames = wf.getnframes()
        audio_bytes = wf.readframes(n_frames)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

    nyquist = 0.5 * RATE
    cutoff = 4000.0
    normal_cutoff = cutoff / nyquist

    b, a = signal.butter(5, normal_cutoff, btype="low", analog=False)
    filtered_audio = signal.lfilter(b, a, audio_data)

    max_val = np.max(np.abs(filtered_audio))
    if max_val > 0:
        normalized_audio = (filtered_audio / max_val) * 26000
    else:
        normalized_audio = filtered_audio

    normalized_audio = normalized_audio.astype(np.int16)

    with wave.open(CLEANED_OUTPUT, "wb") as wf_out:
        wf_out.setparams(params)
        wf_out.writeframes(normalized_audio.tobytes())

    print(f"💾 전처리 완료 파일 저장 완료: {CLEANED_OUTPUT}")


# =========================
# 4. Whisper STT
# =========================

def get_whisper_model():
    global _whisper_model

    if _whisper_model is None:
        print("\n🤖 Whisper Base 모델을 로드하는 중입니다...")
        _whisper_model = whisper.load_model("base")

    return _whisper_model


def run_whisper_test():
    model = get_whisper_model()

    print("🔮 정제된 오디오 파일에서 텍스트(raw_text)를 추출 중입니다...")

    with wave.open(CLEANED_OUTPUT, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    result = model.transcribe(audio_array, fp16=False, language="ko")

    fe_sharing_data = {
        "audio_file": CLEANED_OUTPUT,
        "sampling_rate": int(RATE),
        "raw_text": str(result["text"]).strip()
    }

    print("\n==============================================")
    print("🎉 [FEELtering] 음성 처리 및 STT 완료")
    print("==============================================")
    print(json.dumps(fe_sharing_data, ensure_ascii=False, indent=2))
    print("==============================================")

    return fe_sharing_data


# =========================
# 5. 프론트엔드 버튼 연동용 함수
# =========================

recording_thread = None
stop_event = threading.Event()
recorded_frames = []
recording_stream = None
recording_p = None
is_recording = False
has_detected_speech = False


def frontend_record_loop():
    global recorded_frames, recording_stream, has_detected_speech

    has_spoken = False

    print("🎤 [FEELtering] 프론트엔드 버튼으로 녹음을 시작했습니다.")

    while not stop_event.is_set():
        try:
            data = recording_stream.read(CHUNK, exception_on_overflow=False)
            recorded_frames.append(data)

            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_data_float = audio_data.astype(np.float64)
            energy = np.sqrt(np.mean(audio_data_float ** 2))

            if energy > VAD_THRESHOLD and not has_spoken:
                print("🗣️ 사용자의 발화가 감지되었습니다.")
                has_spoken = True
                has_detected_speech = True

        except Exception as e:
            print("녹음 중 오류:", e)
            break

    print("⏹️ 프론트엔드 버튼으로 녹음을 종료했습니다.")


def start_recording():
    """
    Flask /start-recording 라우트에서 호출.
    프론트엔드에서 녹음 버튼을 처음 눌렀을 때 실행된다.
    """
    global recording_thread, stop_event, recorded_frames
    global recording_stream, recording_p, is_recording
    global has_detected_speech

    if is_recording:
        return {
            "success": False,
            "message": "이미 녹음 중입니다."
        }

    import pyaudio

    recorded_frames = []
    has_detected_speech = False
    stop_event.clear()

    recording_p = pyaudio.PyAudio()

    recording_stream = recording_p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    is_recording = True

    recording_thread = threading.Thread(target=frontend_record_loop)
    recording_thread.start()

    return {
        "success": True,
        "message": "녹음을 시작했습니다."
    }


def stop_recording_and_process():
    """
    Flask /stop-recording 라우트에서 호출.
    프론트엔드에서 녹음 버튼을 다시 눌렀을 때 실행된다.

    실행 순서:
    1. 녹음 종료
    2. raw_input.wav 저장
    3. 전처리
    4. Whisper STT
    5. raw_text 반환
    """
    global recording_thread, stop_event, recorded_frames
    global recording_stream, recording_p, is_recording
    global has_detected_speech

    if not is_recording:
        return {
            "success": False,
            "message": "진행 중인 녹음이 없습니다."
        }

    stop_event.set()

    if recording_thread is not None:
        recording_thread.join()

    import pyaudio

    sample_width = recording_p.get_sample_size(pyaudio.paInt16)

    if recording_stream is not None:
        recording_stream.stop_stream()
        recording_stream.close()

    if recording_p is not None:
        recording_p.terminate()

    is_recording = False

    if not recorded_frames or not has_detected_speech:
        return {
            "success": False,
            "message": "발화가 감지되지 않았습니다. 다시 시도해 주세요."
        }

    wf = wave.open(RAW_OUTPUT, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(b"".join(recorded_frames))
    wf.close()

    print(f"💾 원본 파일 저장 완료: {RAW_OUTPUT}")

    preprocess_audio()
    stt_result = run_whisper_test()

    return {
        "success": True,
        "message": "녹음 및 음성 처리가 완료되었습니다.",
        "audio_file": stt_result["audio_file"],
        "sampling_rate": stt_result["sampling_rate"],
        "raw_text": stt_result["raw_text"]
    }


def is_currently_recording():
    return is_recording


# =========================
# 6. 기존 터미널 단독 실행 모드
# =========================

if __name__ == "__main__":
    record_voice_with_vad()
    preprocess_audio()
    run_whisper_test()
