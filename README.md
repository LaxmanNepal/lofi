# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V3.2 — Story → Lyrics → Music → Master → Stems → Cover → Video → Lyric Video → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Vocal + instrumental separation:** Demucs `htdemucs` on demand
- **Vocal controls:** vocal level, instrumental level and vocal pan, with custom-mix WAV export
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer video
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support, karaoke-style highlighting, intro/outro fades and four visual themes
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Release packaging:** server-side ZIP containing available audio, stems, artwork, SEO and metadata
- **Reusable presets:** Pardeshi, Romantic, Rainy Night and Nepal Atmosphere, plus custom browser-saved presets
- **Batch generation:** up to 20 stories, processed sequentially to avoid concurrent GPU overload
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** `/compose`, `/generate`, `/master`, `/stems`, `/stem-mix`, `/seo`, `/cover`, `/video`, `/lyric-video`, `/package`, `/audio/{file_name}`

### V3.2 lyric video workflow

After generating a song and cover, **AI Lyric Video Engine** can render a 1080p MP4 with the lyrics burned into the video. It supports Devanagari typography, karaoke highlighting, animated cover motion, intro/outro fades and **Night, Warm, Minimal and Nepal** themes.

Because ACE-Step generation currently returns plain lyrics rather than word-level timestamps, V3.2 uses **estimated line timing based on lyric length**. The UI clearly labels this timing as estimated; it is not phoneme-level transcription. A future timestamp editor can provide exact manual/ASR synchronization.

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

## Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art/stems, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. FFmpeg is used for mastering, video rendering and lyric-video rendering. Demucs is used for the optional stem workflow.

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
- V3: creator publishing automation ✅
- V3.1: YouTube video builder ✅
- V3.2: AI lyric video engine with estimated karaoke timing ✅
- V3.3: editable lyric timing + ASR-assisted synchronization
