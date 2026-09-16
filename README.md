# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V3.4 — Story → Lyrics → Music → Master → Stems → Cover → Video → Lyric Video → ASR Sync → Reviewed Sync → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Vocal + instrumental separation:** Demucs `htdemucs` on demand
- **Vocal controls:** vocal level, instrumental level and vocal pan, with custom-mix WAV export
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer video
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support, karaoke-style highlighting, intro/outro fades and four visual themes
- **Lyric synchronization:** faster-whisper ASR on the generated vocal, lyric-line matching, confidence metadata and editable browser timestamps
- **Reviewed synchronization:** V3.4 sends the edited timing rows directly to the lyric-video renderer; valid ASR word timestamps drive word-level karaoke highlights when available
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Release packaging:** server-side ZIP containing available audio, stems, artwork, SEO and metadata
- **Reusable presets:** Pardeshi, Romantic, Rainy Night and Nepal Atmosphere, plus custom browser-saved presets
- **Batch generation:** up to 20 stories, processed sequentially to avoid concurrent GPU overload
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** `/compose`, `/generate`, `/master`, `/stems`, `/stem-mix`, `/seo`, `/cover`, `/video`, `/lyric-timing`, `/lyric-video`, `/package`, `/audio/{file_name}`

### V3.4 reviewed lyric-video workflow

1. Generate the vocal song.
2. Open **Exact Lyric Sync Studio** and run faster-whisper timing.
3. Review/edit every start, end and lyric line.
4. Click **Apply Timing** to keep the reviewed rows in the current generation.
5. In **Final Synchronized Lyric Video**, choose a theme, karaoke mode and waveform setting.
6. Render the 1080p MP4. The renderer uses the reviewed timestamps rather than rebuilding proportional timing.

If ASR word timestamps are available, the final karaoke event uses their actual word durations. If a line has no word timestamps, the renderer distributes the line highlight across its reviewed duration. The renderer still validates timing rows and falls back to estimated timing only when no reviewed timing is supplied.

### V3.3 lyric synchronization workflow

After generating a vocal song, **Exact Lyric Sync Studio** can analyze the vocal with faster-whisper word timestamps, match those ASR segments against the original lyrics, and expose editable start/end times in the browser. Matched lines are marked `asr`; unmatched lines fall back to proportional estimates. This makes the synchronization ASR-assisted rather than pretending that every line is perfectly phoneme-aligned.

The timing engine supports Nepali Devanagari, English and Hindi language selection and caches the Whisper model in memory for reuse during a Colab session.

### V3.2 lyric video workflow

After generating a song and cover, **AI Lyric Video Engine** renders a 1080p MP4 with lyrics burned into the video. It supports Devanagari typography, karaoke highlighting, animated cover motion, intro/outro fades and Night, Warm, Minimal and Nepal themes.

### Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art/stems/video, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. FFmpeg is used for mastering, video rendering and lyric-video rendering. Demucs handles stems and faster-whisper handles optional ASR timing.

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
- V3.3: editable lyric timing + ASR-assisted synchronization ✅
- V3.4: synchronized lyric-video rendering using reviewed timestamps ✅
