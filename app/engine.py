from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from app.emotion import choose_emotion_for_text, prompt_for_emotion, style_for_voice
from app.emotion_clip import load_direct_emotion_clip
from app.persona import build_messages


@dataclass
class ResponseResult:
    reply: str
    emotion: str
    audio: np.ndarray
    sample_rate: int
    is_clip: bool


def generate_reply(
    user_text: str,
    history: list[dict[str, str]],
    llm,
    tts,
    *,
    on_token: Callable[[str], None] | None = None,
) -> ResponseResult:
    """Route the emotion, then either play a direct clip or ask the LLM+TTS for a reply."""
    emotion = choose_emotion_for_text(user_text)

    direct_clip = load_direct_emotion_clip(emotion)
    if direct_clip:
        audio, sample_rate = direct_clip
        return ResponseResult(
            reply=f"[{emotion} clip]",
            emotion=emotion,
            audio=audio,
            sample_rate=sample_rate,
            is_clip=True,
        )

    messages = build_messages(history, user_text, prompt_for_emotion(emotion))
    full_reply = ""
    for token in llm.stream_reply(messages):
        if on_token:
            on_token(token)
        full_reply += token
    reply = full_reply.strip()

    audio, sample_rate = tts.synthesize(style_for_voice(reply, emotion), emotion=emotion)
    return ResponseResult(
        reply=reply,
        emotion=emotion,
        audio=audio,
        sample_rate=sample_rate,
        is_clip=False,
    )
