from app.config import settings
from app.persona import SYSTEM_PROMPT, build_messages


def test_system_prompt_is_always_first():
    messages = build_messages([], "hello")
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}


def test_emotion_prompt_inserted_second_when_provided():
    messages = build_messages([], "hello", "stay flirty")
    assert messages[1] == {"role": "system", "content": "stay flirty"}


def test_emotion_prompt_omitted_when_not_provided():
    messages = build_messages([], "hello")
    assert messages[1] == {"role": "user", "content": "hello"}


def test_user_text_is_always_last():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
    messages = build_messages(history, "how are you", "be nice")
    assert messages[-1] == {"role": "user", "content": "how are you"}


def test_history_included_in_order():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
    messages = build_messages(history, "how are you")
    assert messages[1:3] == history


def test_history_is_trimmed_to_max_history():
    history = [{"role": "user", "content": str(i)} for i in range(settings.max_history + 10)]
    messages = build_messages(history, "final message")
    trimmed = messages[1:-1]
    assert len(trimmed) == settings.max_history
    assert trimmed == history[-settings.max_history :]
