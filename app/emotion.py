import random
import re


EMOTIONS = {
    "warm": {
        "prefixes": ("", "Hey, "),
        "fish_tags": ("[warmly]", "[softly]"),
    },
    "comfort": {
        "prefixes": ("Hey... ", "I know... "),
        "fish_tags": ("[gentle and comforting]", "[empathetic]"),
    },
    "excited": {
        "prefixes": ("Oh! ", "Wait, "),
        "fish_tags": ("[excited]", "[bright and happy]"),
    },
    "playful": {
        "prefixes": ("Okay, ", "Alright, "),
        "fish_tags": ("[playful]", "[teasing gently]"),
    },
    "serious": {
        "prefixes": ("Okay... ", "Listen... "),
        "fish_tags": ("[serious]", "[calm and firm]"),
    },
    "very_angry": {
        "prefixes": ("No... ", "Seriously... "),
        "fish_tags": ("[angry]", "[furious but controlled]"),
    },
    "screaming": {
        "prefixes": ("Hey! ", "Oh my god! "),
        "fish_tags": ("[shouting]", "[panicked shouting]"),
    },
    "horror": {
        "prefixes": ("Wait... ", "Something feels wrong... "),
        "fish_tags": ("[scared whisper]", "[horrified]"),
    },
    "dramatic": {
        "prefixes": ("I need you to hear me... ", "No, listen... "),
        "fish_tags": ("[dramatic]", "[emotional]"),
    },
    "obsessive": {
        "prefixes": ("Don't do that... ", "No, no, listen to me... "),
        "fish_tags": ("[desperate]", "[obsessive and emotional]"),
    },
    "whisper": {
        "prefixes": ("Listen... ", "Come closer... "),
        "fish_tags": ("[whisper]", "[whispers softly]"),
    },
}


RANDOM_EMOTIONS = (
    "warm",
    "comfort",
    "playful",
    "serious",
    "horror",
    "dramatic",
    "dramatic",
    "dramatic",
    "obsessive",
    "obsessive",
    "obsessive",
    "whisper",
    "very_angry",
    "very_angry",
    "screaming",
    "screaming",
    "screaming",
)


OBSESSIVE_LINES = (
    "Why don't you love me like I love you?",
    "Don't leave me alone with that thought.",
    "Say you still want me.",
    "I can be good, I swear.",
    "Look at me when I say this.",
)


def choose_random_emotion() -> str:
    return random.choice(RANDOM_EMOTIONS)


def style_for_voice(text: str, emotion: str) -> str:
    """Nudge prosody with emotion tags and spoken punctuation."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return text

    prefix = random.choice(EMOTIONS.get(emotion, EMOTIONS["warm"])["prefixes"])
    tag = random.choice(EMOTIONS.get(emotion, EMOTIONS["warm"])["fish_tags"])

    if emotion == "comfort":
        text = text.replace(". ", "... ")
        return f"{tag} {prefix}{text}"

    if emotion == "excited":
        text = text.replace(". ", "! ")
        if not text.endswith(("!", "?")):
            text += "!"
        return f"{tag} {prefix}{text}"

    if emotion == "playful":
        return f"{tag} {prefix}{text}"

    if emotion == "serious":
        text = text.replace("!", ".")
        return f"{tag} {prefix}{text}"

    if emotion == "very_angry":
        text = text.replace("! ", ". ")
        return f"{tag} {prefix}{text}"

    if emotion == "screaming":
        text = text.replace(". ", "! ")
        if random.random() < 0.45:
            text = f"{random.choice(OBSESSIVE_LINES)} {text}"
        if not text.endswith(("!", "?")):
            text += "!"
        return f"{tag} {prefix}{text}"

    if emotion == "horror":
        text = text.replace(". ", "... ")
        text = text.replace(", ", "... ")
        return f"{tag} {prefix}{text}"

    if emotion == "dramatic":
        text = text.replace(". ", "... ")
        if random.random() < 0.35:
            text = f"{random.choice(OBSESSIVE_LINES)} {text}"
        if not text.endswith(("!", "?", "...")):
            text += "..."
        return f"{tag} {prefix}{text}"

    if emotion == "obsessive":
        text = text.replace(". ", "... ")
        if random.random() < 0.7:
            text = f"{random.choice(OBSESSIVE_LINES)} {text}"
        if not text.endswith(("!", "?", "...")):
            text += "..."
        return f"{tag} {prefix}{text}"

    if emotion == "whisper":
        text = text.replace(". ", "... ")
        return f"{tag} {prefix}{text.lower()}"

    return f"{tag} {prefix}{text}"
