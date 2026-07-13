
<img width="1080" height="614" alt="1" src="https://github.com/user-attachments/assets/b97e5c66-80c8-461c-a0bf-cb36b37d2499" />

# Nikki

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Runs Locally](https://img.shields.io/badge/runs-100%25%20local-brightgreen.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

Nikki is a fan-made, voice "companion" with Inde Navarrette's voice, based on the movie Obsession by Currie Barker. The idea is simple: you wanted your own Nikki right, for all you pigs who watched the movie and said, "if you're not playing, pass the controller bro." Here you go.

This project turns that bit into a working localhost voice app through which she takes you on a roller coaster of emotions. You speak into the browser, your voice is transcribed locally, Nikki chooses an emotional mode from what you said, a local jailbroken model writes the reply when needed, and Fish Audio gives her a voice. For the most intense modes, she can skip the LLM and Fish completely and play hand-picked audio clips instead.

Her personality is defined in `app/persona.py` (if you want to tweak it) as deeply unstable, obsessive, and manic — just like she is in the movie. A standard LLM simply wouldn't commit to that character. Safety guardrails constantly pull it back, refusing to let her spiral the way she's supposed to. And honestly... where's the fun in that?

That's why I chose **Qwen3-8B-64k-Context-2X-Josiefied-Uncensored** instead. It stays in character far more convincingly, letting Nikki be as unpredictable, unsettling, and emotionally chaotic as she was meant to be.

> And remember... if she threatens you, don't worry. She's just a local voice companion.
>
> ...Probably.
>
> Although, if you catch someone standing in the corner of your room watching you sleep...
>
> Well... that's between you and Nikki.

## Table of Contents

- [Quickstart](#quickstart)
- [Features](#features)
- [Nikki's Personality](#nikkis-personality)
- [Emotion Modes](#emotion-modes)
- [How Emotion Routing Works](#how-emotion-routing-works)
- [Model Stack](#model-stack)
- [Requirements](#requirements)
- [Setup](#setup)
- [Run The Web UI](#run-the-web-ui)
- [Run Terminal Mode](#run-terminal-mode)
- [Optional OpenAI-Compatible Backend](#optional-openai-compatible-backend)
- [Customization](#customization)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

## Quickstart

Already have Ollama installed? This is the fastest path to a working Nikki.

1. Install [Ollama](https://ollama.com), pull the model, and start it:
   ```bash
   ollama pull sebdg/emotional_llama:test
   ollama serve
   ```
2. From the project folder, run the setup script:
   ```bash
   ./setup.sh
   ```
3. Create your env file and add a real Fish Audio key (get one at [fish.audio/app/api-keys](https://fish.audio/app/api-keys/)):
   ```bash
   cp .env.example .env
   ```
4. Start the web app:
   ```bash
   python web.py
   ```
5. Open [http://127.0.0.1:7860](http://127.0.0.1:7860) in Chrome or Edge, allow microphone access, and talk to Nikki.

Want the full picture — manual setup, terminal mode, the OpenAI-compatible backend, troubleshooting? Keep reading below.

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

The app uses five intent-based emotions instead of random emotion spam.

| Mode | Triggered by | Behavior |
| --- | --- | --- |
| `normal` | Ordinary questions that don't match another mode | Fish Audio, eerie / disturbed / off-center delivery |
| `supportive` | "my day is going bad", "I feel sad", "I'm stressed", "I'm tired", "I'm not okay" | Fish Audio, supportive but possessive and emotionally intense |
| `flirting` | "do you miss me", "come over" | Fish Audio, ordinary conversation made disturbing |
| `dramatic` | Disturbing/emotionally loaded topics, incl. the movie-style dad/cancer line ("does your dad really have cancer", "are you scared", "is someone dying", "that was disturbing") | Skips the LLM and Fish Audio when the clip exists, plays `nice-date.mp3` instead |
| `horrifying` | Breakup/abandonment topics ("we should break up", "I'm leaving you", "I don't love you anymore", "we're done") | Skips the LLM and Fish Audio when the clip exists, plays `i-feel-like-you-dont-love-me-as-much-as-i-do.mp3` instead |

## How Emotion Routing Works

The router lives in `app/emotion.py`. The important pieces are:

- `ROUTER_KEYWORDS`: maps user phrases to emotion modes
- `choose_emotion_for_text(user_text)`: chooses the emotion every turn
- `LLM_EMOTION_DIRECTIONS`: tells the LLM how that emotion should color Nikki's delivery
- `style_for_voice(text, emotion)`: adds Fish Audio style tags and punctuation shaping

Direct clip playback lives in `app/emotion_clip.py`. Default clip mapping:

```python
DEFAULT_CLIPS = {
    "dramatic": ROOT / "nice-date.mp3",
    "horrifying": ROOT / "i-feel-like-you-dont-love-me-as-much-as-i-do.mp3",
}
```

The app classifies every new question independently, so Nikki can go from `flirting` to `supportive` to `horrifying` in the same session.

## Model Stack

| Layer | Tech | Notes |
| --- | --- | --- |
| Speech-to-text | [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Default model `base` (config key `WHISPER_MODEL`, also `tiny`/`small`), device via `WHISPER_DEVICE=auto` |
| LLM | Ollama (default) | `Qwen3-8B-64k-Context-2X-Josiefied-Uncensored`, configured via `OLLAMA_BASE_URL` / `OLLAMA_MODEL` |
| Voice / TTS | [Fish Audio](https://fish.audio/) | Model `s2.1-pro-free` (config key `FISH_MODEL`), default reference ID `8fdb1e2c75e6474d9e8f9490670461dc` |

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

| Want to edit... | File |
| --- | --- |
| Nikki's core persona | `app/persona.py` |
| Emotion routing and LLM emotion directions | `app/emotion.py` |
| Direct clip playback | `app/emotion_clip.py` |
| Fish Audio requests | `app/tts.py` |
| Environment defaults | `app/config.py` |

## Project Structure

<details>
<summary>Click to expand the file layout</summary>

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

</details>

## Troubleshooting

<details>
<summary><strong>Fish says <code>401 Unauthorized</code></strong></summary>

Your Fish API key is missing or wrong. Check `.env`:

```env
FISH_API_KEY=your_real_key_here
```

Then restart:

```bash
python web.py
```

</details>

<details>
<summary><strong>Browser says microphone is blocked</strong></summary>

Open the real browser page, not an IDE preview:

```text
http://127.0.0.1:7860
```

Use Chrome or Edge. Click the icon next to the URL and set Microphone to Allow. Then hard refresh with `Cmd + Shift + R`.

</details>

<details>
<summary><strong>Ollama connection refused</strong></summary>

Start Ollama:

```bash
ollama serve
```

Then make sure the model exists:

```bash
ollama list
ollama pull sebdg/emotional_llama:test
```

</details>

<details>
<summary><strong>Direct clips do not play</strong></summary>

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

</details>

<details>
<summary><strong>High RAM usage</strong></summary>

The main local memory users are:

- Faster-Whisper
- Ollama

Use a smaller Whisper model:

```env
WHISPER_MODEL=tiny
```

Or use a smaller Ollama model.

</details>

## Notes

This is a local fan project. Use only voice clips, cloned voices, and generated voices that you have permission to use.

The character is fictional and performative. Keep generated content in that lane.
