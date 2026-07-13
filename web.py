#!/usr/bin/env python3
import base64
import io
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import soundfile as sf

from app.config import settings
from app.engine import generate_reply
from app.llm import ChatLLM
from app.stt import SpeechToText
from app.tts import TextToSpeech


BACKGROUND_IMAGE_PATH = Path(__file__).parent / "1.jpg"
INDEX_HTML_PATH = Path(__file__).parent / "app" / "static" / "index.html"


HOST = "127.0.0.1"
PORT = 7860


INDEX_HTML = INDEX_HTML_PATH.read_text(encoding="utf-8")


class NikkiVoiceApp:
    def __init__(self) -> None:
        print(f"Loading speech recognition ({settings.whisper_model})...")
        self.stt = SpeechToText()
        print("Loading language model connection...")
        self.llm = ChatLLM()
        print("Loading Fish Audio TTS...")
        self.tts = TextToSpeech()
        self.history: list[dict[str, str]] = []
        self.lock = threading.Lock()

    def respond(self, user_text: str) -> dict[str, str]:
        with self.lock:
            result = generate_reply(user_text, self.history, self.llm, self.tts)
            print(f"Selected emotion: {result.emotion}")
            if result.is_clip:
                print(f"Playing direct {result.emotion} clip instead of LLM/Fish.")

            wav = io.BytesIO()
            sf.write(wav, result.audio, result.sample_rate, format="WAV")

            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": result.reply})

            return {
                "reply": result.reply,
                "emotion": result.emotion,
                "audio": base64.b64encode(wav.getvalue()).decode("ascii"),
            }

    def respond_to_audio(self, audio_b64: str) -> dict[str, str]:
        data = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
            f.write(data)

        try:
            heard = self.stt.transcribe_file(path)
        finally:
            path.unlink(missing_ok=True)

        if not heard:
            raise ValueError("I could not hear anything clearly. Try again.")

        result = self.respond(heard)
        result["heard"] = heard
        return result


app: NikkiVoiceApp | None = None
app_lock = threading.Lock()


def get_app() -> NikkiVoiceApp:
    global app
    with app_lock:
        if app is None:
            app = NikkiVoiceApp()
        return app


class Handler(BaseHTTPRequestHandler):
    def _write_response(self, status: int, content_type: str, body: bytes) -> bool:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return True
        except (BrokenPipeError, ConnectionResetError):
            print("Browser disconnected before Nikki finished responding.")
            return False

    def do_GET(self) -> None:
        if self.path == "/":
            body = INDEX_HTML.encode("utf-8")
            self._write_response(200, "text/html; charset=utf-8", body)
            return
        if self.path == "/1.jpg":
            if BACKGROUND_IMAGE_PATH.is_file():
                body = BACKGROUND_IMAGE_PATH.read_bytes()
                self._write_response(200, "image/jpeg", body)
            else:
                self.send_error(404, "1.jpg not found next to web.py")
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/api/respond":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            audio = str(payload.get("audio", "")).strip()
            text = str(payload.get("text", "")).strip()
            if audio:
                result = get_app().respond_to_audio(audio)
            elif text:
                result = get_app().respond(text)
            else:
                raise ValueError("No speech received.")
            body = json.dumps(result).encode("utf-8")
            self._write_response(200, "application/json", body)
        except (BrokenPipeError, ConnectionResetError):
            print("Browser disconnected before Nikki finished responding.")
        except Exception as exc:
            body = str(exc).encode("utf-8")
            self._write_response(500, "text/plain; charset=utf-8", body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    backend = "OpenAI" if settings.use_openai else f"Ollama ({settings.ollama_model})"
    print(f"Nikki voice web is ready with {backend}")
    print(f"Open http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()