# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V2.2 — Story → Lyrics → Music → Master → Stems → Cover → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Vocal + instrumental separation:** Demucs `htdemucs` on demand
- **Vocal controls:** vocal level, instrumental level and vocal pan, with custom-mix WAV export
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Release packaging:** server-side ZIP containing available audio, stems, artwork, SEO and metadata
- **Reusable presets:** Pardeshi, Romantic, Rainy Night and Nepal Atmosphere, plus custom browser-saved presets
- **Batch generation:** up to 20 stories, processed sequentially to avoid concurrent GPU overload
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** `/compose`, `/generate`, `/master`, `/stems`, `/stem-mix`, `/seo`, `/cover`, `/package`, `/audio/{file_name}`

### V2.2 stem workflow

After generating a song, **Vocal + Stem Studio** can run Demucs on the GPU and return separate `VOCALS.wav` and `INSTRUMENTAL.wav` files. The studio also provides vocal level, instrumental level and vocal pan controls. **Export custom mix WAV** renders the adjusted combination server-side.

Stem separation is on-demand because it requires another neural model and GPU memory. Stems remain in the Colab output directory while the runtime is alive and are automatically included in the release ZIP when present.

### Release package

The complete ZIP can contain:

- Original WAV
- Master WAV
- 320 kbps MP3
- Vocals WAV
- Instrumental WAV
- Custom mix WAV
- AI cover PNG
- `youtube-seo.json`
- `youtube-description.txt`
- `metadata.json`
- `README.txt`

## V2.1 features

Reusable presets capture mood, language, voice, duration, tempo, production style and optional story starter. Batch generation accepts one story per line and processes songs sequentially through the real AI endpoints, with a maximum of 20 stories per run.

## Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art/stems, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. The requirements install Demucs for the optional V2.2 stem workflow. FFmpeg is used for mastering and custom stem mixing.

For a permanent production service, use a GPU host you control and protect the API with `LAXMAN_LOFI_API_KEY`.

## Suggested deployment

Host `web/` at `https://apps.laxmannepal.com.np/laxman-lofi/`.

## Roadmap

- V1.1: AI lyric generation + prompt builder ✅
- V1.2: generation history + metadata/seed export ✅
- V1.3: audio mastering + MP3/WAV packaging ✅
- V1.4: cover-art generator + YouTube SEO pack ✅
- V2.0: one-click complete release ZIP ✅
- V2.1: batch generation + reusable presets ✅
- V2.2: vocal controls + stem workflow ✅
- V3: creator publishing automation
