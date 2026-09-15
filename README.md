# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V2.0 — Story → Lyrics → Music → Master → Cover → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Release packaging:** server-side ZIP containing available audio, artwork, SEO and metadata
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** FastAPI endpoints `/compose`, `/generate`, `/master`, `/seo`, `/cover`, `/package`, and `/audio/{file_name}`

### V2 complete release package

After generating a song, the studio can create one portable ZIP containing:

- Original WAV
- Master WAV when mastering has been completed
- 320 kbps MP3 when mastering has been completed
- AI cover PNG when generated
- `youtube-seo.json`
- `youtube-description.txt`
- `metadata.json`
- `README.txt`

The ZIP is generated server-side so the browser does not need a ZIP library. The cover image is sent to the server only for packaging; it is not stored in browser history.

## Workflow

1. Enter a story.
2. Create and review original lyrics.
3. Generate the song with ACE-Step.
4. Master it to WAV/MP3.
5. Generate optional cover art.
6. Generate YouTube SEO.
7. Click **Create complete ZIP**.
8. Keep the package as the release record.

## Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. Diffusers/Safetensors/Pillow are required for optional SDXL cover generation. ZIP packaging uses Python's standard library.

For a permanent production service, use a GPU host you control and protect the API with `LAXMAN_LOFI_API_KEY`.

## Suggested deployment

Host `web/` at `https://apps.laxmannepal.com.np/laxman-lofi/`.

## Roadmap

- V1.1: AI lyric generation + prompt builder ✅
- V1.2: generation history + metadata/seed export ✅
- V1.3: audio mastering + MP3/WAV packaging ✅
- V1.4: cover-art generator + YouTube SEO pack ✅
- V2.0: one-click complete release ZIP ✅
- V2.1: batch generation + reusable presets
- V2.2: vocal controls + stem workflow
- V3: creator publishing automation
