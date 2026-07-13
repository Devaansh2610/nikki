#!/usr/bin/env python3
import base64
import io
import json
import sys
import tempfile
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import soundfile as sf

from app.config import settings
from app.emotion import choose_emotion_for_text, prompt_for_emotion, style_for_voice
from app.emotion_clip import load_direct_emotion_clip
from app.llm import ChatLLM
from app.persona import build_messages
from app.stt import SpeechToText
from app.tts import TextToSpeech


BACKGROUND_IMAGE_PATH = Path(__file__).parent / "1.jpg"


HOST = "127.0.0.1"
PORT = 7860


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nikki Voice</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #101114;
      --panel: #181a20;
      --text: #f4f0e8;
      --muted: #aaa39a;
      --accent: #e85d75;
      --accent-2: #49c6b8;
      --edge: #2c3038;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      position: relative;
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background-image: url("/1.jpg");
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      background-attachment: fixed;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background: rgba(10, 10, 12, 0.35);
      z-index: 0;
    }
    main {
      position: relative;
      z-index: 1;
      width: 100vw;
      min-height: 100vh;
      display: block;
    }
    h1 {
      margin: 0;
      font-size: 34px;
      font-weight: 750;
      letter-spacing: 0;
    }
    .voice {
      position: fixed;
      bottom: 48px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 2;
      width: 64px;
      aspect-ratio: 1;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.16);
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.02)),
        radial-gradient(circle at 50% 42%, var(--accent), #812b7b 58%, #17191f 72%);
      color: white;
      font-size: 11px;
      font-weight: 750;
      letter-spacing: 0;
      cursor: pointer;
      transition: transform 160ms ease, filter 160ms ease, box-shadow 160ms ease;
      box-shadow: 0 10px 28px rgba(232, 93, 117, 0.26);
    }
    .voice:hover { transform: translateX(-50%) translateY(-2px); filter: brightness(1.08); }
    .voice:disabled { cursor: wait; opacity: 0.76; transform: translateX(-50%); }
    .voice.listening {
      animation: pulse 1.1s ease-in-out infinite;
      box-shadow: 0 0 0 12px rgba(232, 93, 117, 0.12), 0 18px 52px rgba(232, 93, 117, 0.32);
    }
    @keyframes pulse {
      0%, 100% { transform: translateX(-50%) scale(1); }
      50% { transform: translateX(-50%) scale(1.04); }
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.04); }
    }
    .status {
      position: fixed;
      bottom: 130px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 2;
      width: min(520px, calc(100vw - 32px));
      min-height: 56px;
      display: grid;
      place-items: center;
      color: var(--muted);
      text-align: center;
      line-height: 1.45;
      font-size: 15px;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
    }
    .heard {
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 2;
      width: min(520px, calc(100vw - 32px));
      min-height: 24px;
      color: color-mix(in srgb, var(--text) 78%, transparent);
      text-align: center;
      font-size: 14px;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
    }
  </style>
</head>
<body>
  <main>
    <button class="voice" id="speak" type="button">Speak</button>
    <div class="status" id="status">Tap Speak and talk to Nikki.</div>
    <div class="heard" id="heard"></div>
  </main>
  <script>
    const button = document.getElementById("speak");
    const statusEl = document.getElementById("status");
    const heardEl = document.getElementById("heard");
    let audio = null;
    let stream = null;
    let context = null;
    let processor = null;
    let source = null;
    let chunks = [];
    let startedAt = 0;
    let silenceStartedAt = 0;
    let hasSpeech = false;

    function updateButton(state) {
      if (state === "recording") {
        button.disabled = false;
        button.textContent = "Stop";
        button.classList.add("listening");
      } else if (state === "busy") {
        button.disabled = true;
        button.textContent = "Speak";
        button.classList.remove("listening");
      } else { // idle
        button.disabled = false;
        button.textContent = "Speak";
        button.classList.remove("listening");
      }
    }

    function encodeWav(samples, sampleRate) {
      const buffer = new ArrayBuffer(44 + samples.length * 2);
      const view = new DataView(buffer);
      const write = (offset, string) => {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
      };
      write(0, "RIFF");
      view.setUint32(4, 36 + samples.length * 2, true);
      write(8, "WAVE");
      write(12, "fmt ");
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      write(36, "data");
      view.setUint32(40, samples.length * 2, true);
      let offset = 44;
      for (const sample of samples) {
        const value = Math.max(-1, Math.min(1, sample));
        view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true);
        offset += 2;
      }
      return new Blob([view], { type: "audio/wav" });
    }

    function blobToBase64(blob) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    }

    function flattenChunks(chunks) {
      const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
      const result = new Float32Array(length);
      let offset = 0;
      for (const chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
      }
      return result;
    }

    async function sendAudio(wavBlob) {
      updateButton("busy");
      statusEl.textContent = "Nikki is listening back... first reply can take a minute while models load.";
      const wav = await blobToBase64(wavBlob);
      const response = await fetch("/api/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio: wav })
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      heardEl.textContent = data.heard || "";
      statusEl.textContent = "Nikki is speaking.";
      if (!audio) {
        audio = new Audio();
      }
      audio.pause();
      audio.src = "data:audio/wav;base64," + data.audio;
      audio.onended = () => {
        statusEl.textContent = "Tap Speak and talk again.";
        updateButton("idle");
      };
      await audio.play();
    }

    async function stopRecording() {
      if (!context) return;
      const activeContext = context;
      context = null; // Prevent re-entry immediately
      if (processor) processor.disconnect();
      if (source) source.disconnect();
      if (stream) stream.getTracks().forEach((track) => track.stop());
      const samples = flattenChunks(chunks);
      const wavBlob = encodeWav(samples, activeContext.sampleRate);
      await activeContext.close();
      processor = null;
      source = null;
      stream = null;
      chunks = [];
      sendAudio(wavBlob).catch((error) => {
        statusEl.textContent = error.message || "Something went wrong.";
        updateButton("idle");
      });
    }

    button.addEventListener("click", async () => {
      try {
        if (stream) {
          await stopRecording();
          return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("This browser context cannot access the microphone.");
        }

        // Pre-unlock the audio element within the user gesture context
        if (!audio) {
          audio = new Audio();
        }
        audio.src = "data:audio/wav;base64,UklGRigAAABXQVZFRm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAAAD";
        audio.play().catch(() => {});

        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        updateButton("recording");
        heardEl.textContent = "";
        statusEl.textContent = "Listening...";
        context = new AudioContext();
        await context.resume();
        source = context.createMediaStreamSource(stream);
        processor = context.createScriptProcessor(4096, 1, 1);
        startedAt = performance.now();
        silenceStartedAt = 0;
        hasSpeech = false;

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          chunks.push(new Float32Array(input));
          const energy = Math.sqrt(input.reduce((sum, value) => sum + value * value, 0) / input.length);
          const now = performance.now();

          if (energy > 0.005) {
            hasSpeech = true;
            silenceStartedAt = 0;
          } else if (hasSpeech && silenceStartedAt === 0) {
            silenceStartedAt = now;
          }

          if ((hasSpeech && silenceStartedAt && now - silenceStartedAt > 1200) || now - startedAt > 20000) {
            stopRecording();
          }
        };

        source.connect(processor);
        processor.connect(context.destination);
      } catch (error) {
        if (stream) stream.getTracks().forEach((track) => track.stop());
        stream = null;
        updateButton("idle");
        statusEl.textContent = "Mic is blocked by this browser context. Open http://127.0.0.1:7860 directly in Chrome or Edge, not inside an IDE preview, then allow Microphone.";
      }
    });
  </script>
</body>
</html>
"""


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
            emotion = choose_emotion_for_text(user_text)
            print(f"Selected emotion: {emotion}")
            direct_clip = load_direct_emotion_clip(emotion)
            if direct_clip:
                print(f"Playing direct {emotion} clip instead of LLM/Fish.")
                audio, sr = direct_clip
                reply = f"[{emotion} clip]"
            else:
                messages = build_messages(self.history, user_text, prompt_for_emotion(emotion))
                reply = "".join(self.llm.stream_reply(messages)).strip()
                audio, sr = self.tts.synthesize(style_for_voice(reply, emotion), emotion=emotion)

            wav = io.BytesIO()
            sf.write(wav, audio, sr, format="WAV")

            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": reply})

            return {
                "reply": reply,
                "emotion": emotion,
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


MAX_REQUEST_BYTES = 25 * 1024 * 1024  # generous cap for a ~20s WAV clip


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
            if length > MAX_REQUEST_BYTES:
                body = b"Request body too large."
                self._write_response(413, "text/plain; charset=utf-8", body)
                return

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
        except (ValueError, RuntimeError) as exc:
            # Deliberately raised with a message that's safe to show the user
            # (e.g. "No speech received.", Fish/Whisper setup errors).
            print(f"Request failed: {exc}")
            body = str(exc).encode("utf-8")
            self._write_response(500, "text/plain; charset=utf-8", body)
        except Exception:
            # Anything else is unexpected - log the real error server-side but
            # don't echo internals (paths, stack traces) back to the client.
            traceback.print_exc()
            body = b"Something went wrong processing your request."
            self._write_response(500, "text/plain; charset=utf-8", body)

    def log_message(self, format: str, *args) -> None:
        return


def _check_backend_ready() -> None:
    """Fail fast at startup instead of on the first request if the LLM backend is down."""
    if settings.use_openai:
        return

    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {settings.ollama_base_url}. "
            f"Start it with `ollama serve` and make sure `{settings.ollama_model}` "
            "is pulled."
        ) from exc


def main() -> None:
    try:
        _check_backend_ready()
    except RuntimeError as exc:
        print(f"\nStartup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    backend = "OpenAI" if settings.use_openai else f"Ollama ({settings.ollama_model})"
    print(f"Nikki voice web is ready with {backend}")
    print(f"Open http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()