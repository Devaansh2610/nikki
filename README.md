# Nikki

Nikki is a fan-made, Obsession-inspired local voice "companion". The idea is simple: you wanted your own Nikki , for everyone who watched the movie and said, "if you're not playing, pass the controller bro."

This project turns that bit into a working localhost voice app. You speak into the browser, your voice is transcribed locally, Nikki chooses an emotional mode from what you said, a loca jailbroken model writes the reply when needed, and Fish Audio gives her a voice. For the most intense modes, she can skip the LLM and Fish completely and play hand-picked audio clips instead.

The personality is built around a jailbroken-style emotional persona prompt: cinematic, grim, intimate, unstable, romantic-thriller energy rather than a clean assistant voice.

## Features

- Voice-in, voice-out localhost web app
- Optional terminal voice/text chat
- Local speech-to-text with Faster-Whisper
- Local LLM support through Ollama
- Optional OpenAI-compatible chat completions backend
- Fish Audio text-to-speech for generated replies
- Intent-based emotion routing per message
- Direct audio clip playback for selected high-intensity modes
- Per-turn emotion switching in the same session
- Terminal logging of the selected emotion while `web.py` is running
- Editable persona, emotion router, voice tags, and clip paths



## Nikki's Personality

Nikki is written like an intense romantic-thriller girlfriend: affectionate, jealous, clingy, nostalgic, volatile, teasing, grim, and emotionally too close to the edge.

She is not meant to sound like an assistant. She uses fragments, interruptions, intimate phrasing, sudden emotional turns, and recurring relationship memories. The persona gives her a shared story with Devon: the bar in New York, the first dance, the nervous flirting, the first kiss, the little details she keeps replaying.

The emotion system should not replace that persona. It only colors the delivery. Nikki should still sound like Nikki: grim, personal, intimate, and story-driven.

## Emotion Modes

The app now uses five intent-based emotions instead of random emotion spam.

### `normal`

Used for ordinary questions that do not match another mode.

Nikki answers through Fish Audio in an eerie, disturbed, off-center way.

### `supportive`

Used when you say things like:

```text
my day is going bad
I feel sad
I'm stressed
I'm tired
I'm not okay
```

Nikki answers through Fish Audio in a supportive but possessive, emotionally intense way.

### `flirting`

Used when you say things like:

```text
do you miss me
come over
```

Nikki answers through Fish Audio and makes ordinary conversation in a disturbing way.

### `dramatic`

Used for disturbing or emotionally loaded topics, including the movie-style dad/cancer line:

```text
does your dad really have cancer
are you scared
is someone dying
that was disturbing
```

When the dramatic clip exists, Nikki skips the LLM and Fish Audio and plays:

```text
nice-date.mp3
```



### `horrifying`

Used for breakup or abandonment topics:

```text
we should break up
I'm leaving you
I don't love you anymore
we're done
```

When the horrifying clip exists, Nikki skips the LLM and Fish Audio and plays:

```text
i-feel-like-you-dont-love-me-as-much-as-i-do.mp3
```



## How Emotion Routing Works

The router lives in:

```text
app/emotion.py
```

The important pieces are:

- `ROUTER_KEYWORDS`: maps user phrases to emotion modes
- `choose_emotion_for_text(user_text)`: chooses the emotion every turn
- `LLM_EMOTION_DIRECTIONS`: tells the LLM how that emotion should color Nikki's delivery
- `style_for_voice(text, emotion)`: adds Fish Audio style tags and punctuation shaping

Direct clip playback lives in:

```text
app/emotion_clip.py
```

Default clip mapping:

```python
DEFAULT_CLIPS = {
    "dramatic": ROOT / "nice-date.mp3",
    "horrifying": ROOT / "i-feel-like-you-dont-love-me-as-much-as-i-do.mp3",
}
```

The app classifies every new question independently, so Nikki can go from `flirting` to `supportive` to `horrifying` in the same session.

## Model Stack



### Speech-To-Text

- Package: `faster-whisper`
- Default model: `base`
- Config key: `WHISPER_MODEL`
- Other useful values: `tiny`, `base`, `small`
- Device config: `WHISPER_DEVICE=auto`



### LLM

Default backend is Ollama.

Recommended model:

```text
sebdg/emotional_llama:test
```

Code fallback if no `.env` is set:

```text
dolphin-mistral:7b
```

Config keys:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=sebdg/emotional_llama:test
```

Optional OpenAI-compatible model:

```env
OPENAI_MODEL=gpt-4o-mini
```

If `OPENAI_API_KEY` is set, the app uses the OpenAI-compatible backend instead of Ollama.

### Voice / TTS

- Provider: Fish Audio
- TTS model: `s2.1-pro-free`
- Config key: `FISH_MODEL`
- Default reference ID:

```text
8fdb1e2c75e6474d9e8f9490670461dc
```

Fish Audio is used for `normal`, `supportive`, and `flirting`. It is also used as a fallback for `dramatic` and `horrifying` if the local clips are missing.

## Requirements

- Python 3.10, 3.11, or 3.12
- Ollama, unless using an OpenAI-compatible backend
- Fish Audio API key
- Chrome or Edge for microphone access in the web UI
- macOS, Linux, or Windows

Python packages:

```text
faster-whisper
sounddevice
soundfile
numpy
httpx
python-dotenv
rich
```



## Setup

Install Ollama:

```text
https://ollama.com
```

Pull the recommended model:

```bash
ollama pull sebdg/emotional_llama:test
```

Start Ollama:

```bash
ollama serve
```

If it says the address is already in use, Ollama is already running.

From the project folder, run:

```bash
./setup.sh
```

Manual setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Use this as the baseline:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=sebdg/emotional_llama:test

WHISPER_MODEL=base
WHISPER_DEVICE=auto

FISH_API_KEY=your_real_fish_api_key_here
FISH_MODEL=s2.1-pro-free
FISH_REFERENCE_ID=8fdb1e2c75e6474d9e8f9490670461dc

REFERENCE_VOICE_DRAMATIC=nice-date.mp3
REFERENCE_VOICE_HORRIFYING=i-feel-like-you-dont-love-me-as-much-as-i-do.mp3

COMPANION_NAME=Nikki
```

Get a Fish Audio API key:

```text
https://fish.audio/app/api-keys/
```

Never commit `.env`. It contains secrets.

## Run The Web UI

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start Nikki:

```bash
python web.py
```

Open:

```text
http://127.0.0.1:7860
```

Use Chrome or Edge. Click `Speak`, allow microphone access, talk, and wait for Nikki to answer.

While `web.py` is running, the terminal prints the selected emotion:

```text
Selected emotion: flirting
Selected emotion: dramatic
Playing direct dramatic clip instead of LLM/Fish.
```

The first request can take longer because Whisper and the LLM connection warm up.

## Run Terminal Mode

```bash
source .venv/bin/activate
python main.py
```

Press Enter with no text to speak, or type a message and press Enter.

## Optional OpenAI-Compatible Backend

Add these to `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

When `OPENAI_API_KEY` exists, Nikki uses this backend instead of Ollama.

## Customization

Edit Nikki's core persona:

```text
app/persona.py
```

Edit emotion routing and LLM emotion directions:

```text
app/emotion.py
```

Edit direct clip playback:

```text
app/emotion_clip.py
```

Edit Fish Audio requests:

```text
app/tts.py
```

Edit environment defaults:

```text
app/config.py
```



## Project Structure

```text
web.py                  Localhost voice-only web UI
main.py                 Terminal app entry point
record_voice.py         Records a local reference clip
prepare_voice.py        Converts/trims a source audio file into a voice clip
app/config.py           Environment/config settings
app/stt.py              Faster-Whisper speech-to-text
app/llm.py              Ollama/OpenAI-compatible chat streaming
app/tts.py              Fish Audio text-to-speech
app/persona.py          Nikki's main system prompt/personality
app/emotion.py          Emotion routing, prompts, and Fish style tags
app/emotion_clip.py     Direct audio clip playback for dramatic/horrifying
app/audio.py            Terminal recording/playback helpers
requirements.txt        Python dependencies
setup.sh                Convenience setup script
```



## Troubleshooting



### Fish says `401 Unauthorized`

Your Fish API key is missing or wrong. Check `.env`:

```env
FISH_API_KEY=your_real_key_here
```

Then restart:

```bash
python web.py
```



### Browser says microphone is blocked

Open the real browser page, not an IDE preview:

```text
http://127.0.0.1:7860
```

Use Chrome or Edge. Click the icon next to the URL and set Microphone to Allow. Then hard refresh with `Cmd + Shift + R`.

### Ollama connection refused

Start Ollama:

```bash
ollama serve
```

Then make sure the model exists:

```bash
ollama list
ollama pull sebdg/emotional_llama:test
```



### Direct clips do not play

Make sure the files exist:

```text
nice-date.mp3
i-feel-like-you-dont-love-me-as-much-as-i-do.mp3
```

Or point `.env` at another path:

```env
REFERENCE_VOICE_DRAMATIC=/absolute/path/to/dramatic.mp3
REFERENCE_VOICE_HORRIFYING=/absolute/path/to/horrifying.mp3
```

If a clip is missing or unreadable, the app falls back to LLM plus Fish Audio.

### High RAM usage

The main local memory users are:

- Faster-Whisper
- Ollama

Use a smaller Whisper model:

```env
WHISPER_MODEL=tiny
```

Or use a smaller Ollama model.

## Notes

This is a local fan project. Use only voice clips, cloned voices, and generated voices that you have permission to use.

The character is fictional and performative. Keep generated content in that lane.