import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "hf.co/mradermacher/Qwen3-8B-64k-Context-2X-Josiefied-Uncensored-i1-GGUF:Q5_K_M").strip()

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "auto")

    tts_backend: str = "fish"
    fish_api_key: str | None = os.getenv("FISH_API_KEY")
    fish_model: str = os.getenv("FISH_MODEL", "s2.1-pro-free").strip()
    fish_reference_id: str = os.getenv(
        "FISH_REFERENCE_ID", "8fdb1e2c75e6474d9e8f9490670461dc"
    ).strip()
    fish_base_url: str = os.getenv("FISH_BASE_URL", "https://api.fish.audio")

    reference_voice: Path = Path(os.getenv("REFERENCE_VOICE", "voices/reference.wav"))
    companion_name: str = os.getenv("COMPANION_NAME", "Nikki")

    sample_rate: int = 16_000
    max_history: int = 20

    @property
    def use_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def reference_voice_path(self) -> Path:
        path = self.reference_voice
        if not path.is_absolute():
            path = ROOT / path
        return path

    def emotion_voice_path(self, emotion: str) -> Path:
        env_name = f"REFERENCE_VOICE_{emotion.upper()}"
        path = Path(os.getenv(env_name, f"voices/{emotion}.wav"))
        if not path.is_absolute():
            path = ROOT / path
        return path

    def fish_reference_id_for_emotion(self, emotion: str | None) -> str:
        if not emotion:
            return self.fish_reference_id
        env_name = f"FISH_REFERENCE_ID_{emotion.upper()}"
        return os.getenv(env_name, self.fish_reference_id).strip()


settings = Settings()
