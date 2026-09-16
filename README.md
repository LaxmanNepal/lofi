# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V4.1 — Story → Lyrics → Music → Stems → Vocal Enhance → Mix → Smart Arrange → Structure → Section-Aware Arrangement → Stem-Aware Arrangement → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** deterministic FFmpeg DSP
- **Stems:** Demucs `htdemucs` on demand
- **Vocal enhancement:** noise reduction, dynamics, presence and de-essing-style processing
- **Mix + master:** stem balance, EQ, compression, stereo width and loudness normalization
- **Smart Arrangement V3.8:** FFmpeg/FFprobe energy analysis, heuristic verse/build/chorus labels, optional leading/trailing silence trimming, intro/outro fades and conservative chorus-energy lift
- **Song Structure V3.9:** editable Intro/Verse/Pre-Chorus/Chorus/Bridge/Final Chorus/Outro timeline inferred from energy and position
- **Section-Aware Arrangement V4.0:** browser-side OfflineAudioContext rendering applies section-specific gain, EQ emphasis, stereo-aware transitions and profile controls to the reviewed structure
- **Stem-Aware Arrangement V4.1:** analyzes Demucs vocal and instrumental energy independently, then applies section-specific vocal/instrumental gains, chorus lifts, bridge reduction, vocal sidechain ducking, stereo-width shaping and final loudness normalization
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support and karaoke highlighting
- **Lyric synchronization:** faster-whisper ASR with editable timing
- **Audio quality:** loudness, peak, duration and silence inspection
- **Export:** WAV 24-bit / 44.1 kHz and MP3 320 kbps where applicable

### V4.1 stem-aware controls

- Vocal level
- Instrumental level
- Chorus vocal lift
- Chorus instrumental lift
- Bridge reduction
- Vocal ducking via FFmpeg sidechain compression
- Stereo width
- Target loudness
- Separate vocal and instrumental energy timelines
- Reuses the reviewed V3.9 structure when available
- Backend-rendered 24-bit WAV + 320 kbps MP3

V4.1 intentionally does **not** synthesize new instruments or voices. It processes the existing Demucs stems independently, making the section changes reproducible and inspectable. Stem separation remains model-dependent, so review the resulting vocal/instrumental balance before publishing.

### V4.1 API

- `POST /stem-arrangement/analyze` — inspect vocal and instrumental energy separately
- `POST /stem-arrangement` — render the reviewed structure through the separate stems

### V3.8 API

- `POST /arrangement/analyze` — inspect energy and heuristic sections
- `POST /arrangement` — build the smart-arranged WAV + MP3

Section detection is **heuristic**, based on audio energy; it is not claimed to be perfect musical transcription. Review the arrangement before publishing.

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key.
