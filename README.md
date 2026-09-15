# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V1.1 — Story → AI Lyrics → Music

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model, default `ministral/Ministral-3b-instruct`
- **Music engine:** ACE-Step v1 3.5B (`ACE-Step/ACE-Step-v1-3.5B`)
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** one user-controlled FastAPI server for `/compose` and `/generate`
- **VRAM strategy:** lyric model is unloaded before ACE-Step generation so the two models do not need to occupy the GPU simultaneously

The current Hugging Face model cards list both the default Ministral 3B lyric model and ACE-Step v1 3.5B as Apache-2.0. ACE-Step v1 is documented as a text-to-music model with structured lyrics/vocal generation. Always verify the current model cards, model components, applicable law, and YouTube policies before commercial distribution.

## How it works

1. Enter a story such as a migrant-worker, relationship, rain, mother, hometown, or night-shift experience.
2. Select mood, language, vocal type, duration and production style.
3. Click **✨ Create AI lyrics**.
4. Edit the generated title/lyrics if needed.
5. Click **Generate song**.
6. The backend uses ACE-Step to render the audio and returns a WAV file.

The system does **not** silently invent a fake demo result. The AI lyric endpoint is real model inference and the music endpoint is real ACE-Step inference.

## Important originality / licensing note

An Apache-2.0 model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics and audio, avoid requests to imitate named artists or existing songs, and keep generation metadata such as model version, prompt, lyrics and seed.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. The notebook installs the lyric-model dependencies, ACE-Step, starts the API and exposes it through a temporary Cloudflare quick tunnel.

For a permanent production service, move the backend to a GPU host you control and protect the API with `LAXMAN_LOFI_API_KEY`.

## Suggested deployment

Host `web/` at:

`https://apps.laxmannepal.com.np/laxman-lofi/`

## Roadmap

- V1.1: AI lyric generation + prompt builder ✅
- V1.2: generation history + metadata/seed export
- V1.3: audio mastering + MP3/WAV packaging
- V1.4: cover-art generator + YouTube SEO pack
- V2: one-click Story → Lyrics → Song → Cover → YouTube package
