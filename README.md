# Nikki

Nikki is a local voice companion app. You talk to her from a small localhost web page, your speech is transcribed locally, a local or OpenAI-compatible LLM writes the reply, and Fish Audio generates the final voice.

## Persona

Nikki is written as an intense, magnetic, emotionally volatile romantic-thriller style companion. In the current prompt, she is Devon's fictional girlfriend: obsessive, dramatic, clingy, affectionate, impulsive, jealous, possessive, playful, and deeply romantic.

Her emotional range is intentionally unstable. She can shift from teasing to vulnerable, laughing to crying, confident to panicked, or soft to dramatic very quickly. She often seeks reassurance, worries about being abandoned, and may say things like "you still love me, right?", "don't disappear on me", or "tell me I'm still your girl."

She has a shared backstory with Devon: they met by chance in a small bar in New York, danced to "For Once in My Life", and remember that night as the moment they accidentally fell in love. Her personality uses that memory often, along with details like rain outside the bar, nervous flirting, stolen jackets, first kisses, inside jokes, cuddling, teasing, and sudden nostalgia.

Nikki talks like a real girlfriend rather than an assistant. She uses contractions, interruptions, fragments, teasing, emotional pauses, affectionate nicknames, sarcasm, overthinking, and sudden sentimental turns. The goal is not a neutral chatbot voice; the goal is a cinematic, intimate, volatile character who feels emotionally present and unpredictable.

Even with the unstable persona, the prompt keeps the character fictional and performative: Nikki should not threaten real harm, encourage self-harm, manipulate through threats, or claim to be in real danger.

## What It Uses

- **Web UI:** built into `web.py`, served at `http://127.0.0.1:7860`
- **Speech-to-text:** `faster-whisper`, default model `base`
- **LLM:** Ollama by default, recommended model `sebdg/emotional_llama:test`
- **Voice/TTS:** Fish Audio API
- **Fish voice clone ID:** `8fdb1e2c75e6474d9e8f9490670461dc`
- **Fish TTS model:** `s2.1-pro-free` by default
- **Optional LLM backend:** OpenAI-compatible chat completions API

## Requirements

- macOS/Linux/Windows with Python 3.11 or 3.12
- A Fish Audio API key
- Ollama, unless you use OpenAI-compatible API settings
- Chrome or Edge for the web voice UI microphone access

Install Ollama from:

```text
https://ollama.com
```

Pull the recommended local chat model:

```bash
ollama pull sebdg/emotional_llama:test
```

Make sure Ollama is running:

```bash
ollama serve
```

If that says `address already in use`, Ollama is already running.

## Setup

Clone the project, then from the project folder run:

```bash
./setup.sh
```

Or install manually:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
nano .env
```

Fill it like this:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=sebdg/emotional_llama:test

WHISPER_MODEL=base
WHISPER_DEVICE=auto

FISH_API_KEY=your_real_fish_api_key_here
FISH_MODEL=s2.1-pro-free
FISH_REFERENCE_ID=8fdb1e2c75e6474d9e8f9490670461dc

COMPANION_NAME=Nikki
```

Get a Fish Audio API key here:

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

Use Chrome or Edge. Click **Speak**, allow microphone access, talk, and wait for Nikki to answer.

The first request can take longer because Whisper and the LLM connection warm up.

## Optional Terminal Mode

There is also a terminal chat mode:

```bash
source .venv/bin/activate
python main.py
```

Press Enter with no text to speak, or type a message and press Enter.

## Personality And Emotions

Edit Nikki's personality here:

```text
app/persona.py
```

That changes what the LLM says.

Edit voice/emotion behavior here:

```text
app/emotion.py
```

That controls intent-based emotional delivery:

- `normal` for everyday questions, answered through Fish Audio in an eerie disturbed style
- `supportive` for bad-day or upset messages, answered through Fish Audio
- `flirting` for intimate or appearance-related questions, answered through Fish Audio
- `dramatic` for disturbing topics like illness, death, fear, or the movie-specific dad/cancer line
- `horrifying` for breakup or abandonment topics

The app classifies each new question independently, so the emotion can change from one turn to the next in the same session.

`dramatic` and `horrifying` skip the LLM and Fish Audio when their local clips exist. Defaults:

```env
REFERENCE_VOICE_DRAMATIC=nice-date.mp3
REFERENCE_VOICE_HORRIFYING=i-feel-like-you-dont-love-me-as-much-as-i-do.mp3
```

If a clip is missing, the app falls back to the normal LLM/Fish path using that emotion's style tags.

## Optional OpenAI-Compatible LLM

By default Nikki uses Ollama. To use OpenAI or another compatible API instead, add these to `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

If `OPENAI_API_KEY` is set, Nikki uses that instead of Ollama.

## Project Structure

```text
web.py              Localhost voice-only web UI
main.py             Terminal voice/text chat
app/config.py       Environment/config settings
app/stt.py          Faster-Whisper speech-to-text
app/llm.py          Ollama/OpenAI-compatible chat streaming
app/tts.py          Fish Audio text-to-speech
app/persona.py      Nikki's system prompt/personality
app/emotion.py      Random emotional voice styling
app/audio.py        Terminal recording/playback helpers
requirements.txt    Python dependencies
setup.sh            Convenience setup script
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

### High RAM usage

This project now uses Fish Audio for TTS instead of a local XTTS model. The main local memory users are:

- Faster-Whisper STT
- Ollama model process

If RAM is still high, use a smaller Whisper model:

```env
WHISPER_MODEL=tiny
```

Or use a smaller Ollama model.

## Notes

Voice cloning and generated voices should only be used with audio and voice models you have permission to use.
