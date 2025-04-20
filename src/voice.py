import sounddevice as sd, soundfile as sf, io, os, webrtcvad
from google.cloud import speech, texttospeech
from pydub import AudioSegment, silence
import os

SAMPLE_RATE = 48000        # ↩︎ compat. webrtcvad
FRAME_MS    = 10           # 10 ms
FRAME_BYTES = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 16 bit PCM → 2 octets

VAD = webrtcvad.Vad(int(os.getenv("VAD_MODE", 3)))

def record_chunk(seconds: int = 5, sr: int = SAMPLE_RATE):
    audio = sd.rec(int(seconds * sr), samplerate=sr,
                   channels=1, dtype="int16")
    sd.wait()
    return audio

def detect_silence(chunk, sr: int = SAMPLE_RATE) -> bool:
    raw = chunk.tobytes()
    for i in range(0, len(raw), FRAME_BYTES):
        frame = raw[i : i + FRAME_BYTES]
        if len(frame) < FRAME_BYTES:
            break
        if VAD.is_speech(frame, sr):
            return False        # on entend de la voix
    return True                 # silence total

def transcribe(chunk, sr=44100) -> str:
    tmp = io.BytesIO()
    sf.write(tmp, chunk, sr, format="FLAC")
    client = speech.SpeechClient()
    response = client.recognize(
        config=speech.RecognitionConfig(language_code="fr-FR", sample_rate_hertz=sr),
        audio=speech.RecognitionAudio(content=tmp.getvalue()),
    )
    return response.results[0].alternatives[0].transcript if response.results else ""


# Choisis une voix FR compatible SSML (Wavenet ou Standard)
VOICE_NAME = os.getenv("GOOGLE_TTS_VOICE", "fr-FR-Wavenet-D")  # ← clé d'environnement optionnelle

def speak(ssml: str):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name=os.getenv("GOOGLE_TTS_VOICE", "fr-FR-Wavenet-D"),
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    # --- DEBUG ---------------------------------------------------------
    # print(f"[TTS] bytes reçus : {len(response.audio_content)}")
    # -------------------------------------------------------------------

    with open("output.mp3", "wb") as f:
        f.write(response.audio_content)

    os.system("mpg123 output.mp3")


