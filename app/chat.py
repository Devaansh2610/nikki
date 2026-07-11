from rich.console import Console
from rich.panel import Panel

from app.audio import AudioPlayer, record_until_silence
from app.config import settings
from app.emotion import choose_emotion_for_text, prompt_for_emotion, style_for_voice
from app.emotion_clip import load_direct_emotion_clip
from app.llm import ChatLLM
from app.persona import build_messages

console = Console()


class NikkiChat:
    def __init__(self) -> None:
        console.print(
            f"[dim]Loading speech recognition ({settings.whisper_model})... "
            "first run may download model files[/]"
        )
        from app.stt import SpeechToText

        self.stt = SpeechToText()
        console.print("[dim]Loading language model connection...[/]")
        self.llm = ChatLLM()
        console.print("[dim]Loading Fish Audio TTS...[/]")
        from app.tts import TextToSpeech

        self.tts = TextToSpeech()

        self.history: list[dict[str, str]] = []
        self.player = AudioPlayer()

    def run(self) -> None:
        name = settings.companion_name
        backend = "OpenAI" if settings.use_openai else f"Ollama ({settings.ollama_model})"
        console.print(
            Panel(
                f"[bold]{name}[/] is ready - {backend}\n\n"
                "- Press [cyan]Enter[/] with no text to speak\n"
                "- Or type a message and press Enter\n"
                "- Type [cyan]quit[/] to exit",
                title="Nikki",
                border_style="magenta",
            )
        )

        try:
            while True:
                user_input = console.input("\n[bold green]You[/]: ").strip()

                if user_input.lower() in {"quit", "exit", "q"}:
                    console.print("[dim]Goodbye.[/]")
                    break

                user_text = self._listen() if user_input == "" else user_input
                if not user_text:
                    console.print("[dim]Didn't catch that - try again.[/]")
                    continue

                if user_input == "":
                    console.print(f"[bold green]You[/]: {user_text}")

                self._respond(user_text)
        finally:
            self.player.stop()
            self.llm.close()

    def _listen(self) -> str:
        console.print("[yellow]Speak now...[/]")
        audio = record_until_silence()
        if len(audio) == 0:
            return ""
        console.print("[dim]Transcribing...[/]", end="\r")
        text = self.stt.transcribe(audio)
        console.print(" " * 20, end="\r")
        return text

    def _respond(self, user_text: str) -> None:
        emotion = choose_emotion_for_text(user_text)
        name = settings.companion_name

        console.print(f"[bold magenta]{name}[/] [dim]({emotion})[/]: ", end="")
        direct_clip = load_direct_emotion_clip(emotion)
        if direct_clip:
            audio, sr = direct_clip
            full_reply = f"[{emotion} clip]"
            console.print(full_reply)
            self.player.play(audio, sr)
            self.player.wait_until_done()
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": full_reply})
            return

        messages = build_messages(self.history, user_text, prompt_for_emotion(emotion))
        full_reply = ""

        for token in self.llm.stream_reply(messages):
            console.print(token, end="")
            full_reply += token

        console.print()
        audio, sr = self.tts.synthesize(style_for_voice(full_reply, emotion), emotion=emotion)
        if len(audio) > 0:
            self.player.play(audio, sr)
            self.player.wait_until_done()

        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": full_reply.strip()})
