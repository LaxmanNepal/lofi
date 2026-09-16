# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V3.7 — Story → Lyrics → Music → Stems → Vocal Enhance → Mix → Master → Cover → Video → Lyric Video → ASR Sync → Reviewed Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** FFmpeg mastering
- **Vocal + instrumental separation:** Demucs `htdemucs` on demand
- **Vocal enhancement:** deterministic FFmpeg DSP for noise reduction, room/reverb control, breath dynamics, presence and de-essing-style processing
- **Mix + master:** automatic FFmpeg DSP for stem balance, vocal cleanup, EQ, compression, de-essing-style control, stereo width and loudness normalization
- **Vocal controls:** vocal level, instrumental level and vocal pan, with custom-mix WAV export
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer video
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support, karaoke-style highlighting, intro/outro fades and four visual themes
- **Lyric synchronization:** faster-whisper ASR on the generated vocal, lyric-line matching, confidence metadata and editable browser timestamps
- **Reviewed synchronization:** V3.4 sends edited timing rows directly to the lyric-video renderer; valid ASR word timestamps drive word-level karaoke highlights when available
- **Audio quality:** V3.5 automated pre-publish inspection for loudness, peak level, duration and long silent regions
- **YouTube SEO:** local AI-generated title, description, tags, hashtags and short share copy
- **Release packaging:** server-side ZIP containing available audio, stems, artwork, SEO and metadata
- **Reusable presets:** Pardeshi, Romantic, Rainy Night and Nepal Atmosphere, plus custom browser-saved presets
- **Batch generation:** up to 20 stories, processed sequentially to avoid concurrent GPU overload
- **Cloud runner:** Google Colab notebook in `backend/`
- **API:** `/compose`, `/generate`, `/master`, `/stems`, `/stem-mix`, `/vocal-enhance`, `/mix-master`, `/seo`, `/cover`, `/video`, `/lyric-timing`, `/lyric-video`, `/package`, `/audio/{file_name}`

### V3.7 Vocal Enhancement workflow

1. Generate the vocal song and run **Vocal + Stem Studio**.
2. Open **Vocal Enhancement & Repair Studio**.
3. Adjust noise reduction, room/reverb control, breath dynamics, presence and de-essing.
4. Render the enhanced 44.1 kHz 24-bit vocal WAV.
5. Use the resulting vocal as the cleaned source for your mix/master workflow and listen for artifacts.

V3.7 uses deterministic FFmpeg spectral and dynamic processing. It is intentionally not described as a generative AI voice enhancer. Strong settings can introduce pumping, dullness or other artifacts, so the enhanced stem should be auditioned before release.

### V3.6 Mix & Master workflow

1. Generate the song and run **Vocal + Stem Studio** to create vocals and instrumental stems.
2. Open **AI Mix & Master Studio**.
3. Adjust vocal/instrumental balance and vocal pan.
4. Tune cleanup, warmth, presence, compression, de-essing, stereo width and final loudness target.
5. Build the final 44.1 kHz 24-bit WAV master and 320 kbps MP3.
6. Listen to the result, then run Audio Quality Studio before publishing.

V3.6 is intentionally deterministic DSP rather than a generative model. This keeps the workflow reproducible and avoids adding another large model dependency.

### Originality / licensing

A model license does not guarantee that every generated output is copyrightable, unique, or free of similarity claims. Use original stories/prompts, review generated lyrics/audio/art/stems/video, avoid requests to imitate named artists or existing songs, and keep generation metadata.

## Colab

Open `backend/Laxman_Lofi_AI_Studio_Colab.ipynb` in Google Colab with a GPU. FFmpeg is used for mastering, video rendering, lyric-video rendering, V3.6 mix/master processing and V3.7 vocal enhancement. Demucs handles stems and faster-whisper handles optional ASR timing.

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
- V3.5: audio quality studio + pre-publish checks ✅
- V3.6: automatic mix + master studio ✅
- V3.7: vocal enhancement & repair studio ✅
