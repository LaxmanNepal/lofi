# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V1.4 — Story → AI Lyrics → Music → Master → Cover → YouTube SEO

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model, default `ministral/Ministral-3b-instruct`
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** FastAPI endpoints `/compose`, `/generate`, `/master`, `/seo`, `/cover`, and `/audio/{file_name}`

### V1.4 additions

After a song is generated and mastered, the studio can:

1. Generate original 16:9 cover artwork with SDXL.
2. Reuse the song title, story and mood as the cover context.
3. Generate a YouTube title, description, tags, hashtags and short sharing copy.
4. Copy the complete SEO pack directly from the browser.

Cover generation is intentionally text-free so title typography can be added cleanly in a thumbnail editor. SDXL is optional and requires a CUDA GPU; the music/lyrics workflow remains usable without it.

## V1.3 mastering

The **Master audio** step creates a 44.1 kHz, 24-bit stereo WAV master and 320 kbps MP3 with an approximate −14 LUFS / −1 dBTP production target and configurable fades.

## How it works

1. Enter a story such as a migrant-worker, relationship, rain, mother, hometown, or night-shift experience.
2. Select mood, language, vocal type, duration and production style.
3. Create AI lyrics and review/edit them.
4. Generate the original song with ACE-Step.
5. Master it to WAV/MP3.
6. Generate cover art and YouTube SEO metadata.
7. Keep the prompt, lyrics, model and seed as the project creation record.

## Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. The backend requirements now include Diffusers/Safetensors/Pillow for optional SDXL cover generation.

For a permanent production service, use a GPU host you control and protect the API with `LAXMAN_LOFI_API_KEY`.

## Suggested deployment

Host `web/` at `https://apps.laxmannepal.com.np/laxman-lofi/`.

## Roadmap

- V1.1: AI lyric generation + prompt builder ✅
- V1.2: generation history + metadata/seed export ✅
- V1.3: audio mastering + MP3/WAV packaging ✅
- V1.4: cover-art generator + YouTube SEO pack ✅
- V2: one-click Story → Lyrics → Song → Cover → YouTube package
