# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V4.5 — Story → Lyrics → Music → 4 Stems → Vocal Enhance → Mix → Smart Arrange → Structure → Section-Aware Arrangement → Stem-Aware Arrangement → Instrument Stem Intelligence → Beat & Tempo Intelligence → Rhythm-Aware Arrangement → Groove & Humanization → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** deterministic FFmpeg DSP + browser OfflineAudioContext
- **Stems:** Demucs `htdemucs` on demand
- **Vocal enhancement:** noise reduction, dynamics, presence and de-essing-style processing
- **Mix + master:** stem balance, EQ, compression, stereo width and loudness normalization
- **Smart Arrangement V3.8:** FFmpeg/FFprobe energy analysis and heuristic section shaping
- **Song Structure V3.9:** editable Intro/Verse/Pre-Chorus/Chorus/Bridge/Final Chorus/Outro timeline
- **Section-Aware Arrangement V4.0:** browser OfflineAudioContext section-specific gain/EQ/transitions
- **Stem-Aware Arrangement V4.1:** independent vocal/instrumental section gains, chorus lifts, bridge reduction and ducking
- **Instrument Stem Intelligence V4.2:** full Demucs vocals/drums/bass/other separation with independent energy timelines and section-aware stem automation
- **Beat & Tempo Intelligence V4.3:** estimated BPM, beat grid, 4/4 bar map and reviewed section snapping
- **Rhythm-Aware Arrangement V4.4:** beat/bar-synced gain automation, existing-drum accents, chorus lifts, bass/melody transitions, vocal ducking and bar-aligned fades
- **Groove & Humanization V4.5:** selectable Lofi/Chill/Boom-Bap/Cinematic profiles, deterministic swing offsets, micro-timing map and subtle beat-synchronous gain accents
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support and karaoke highlighting
- **Lyric synchronization:** faster-whisper ASR with editable timing
- **Audio quality:** loudness, peak, duration and silence inspection
- **Export:** WAV 24-bit / 44.1 kHz and MP3 320 kbps where applicable

### V4.5 groove controls

- Lofi, Chill, Boom-Bap and Cinematic groove profiles
- Humanization amount
- Independent drum pulse, bass movement and melody movement controls
- Repeatable seed for deterministic results
- Groove beat map with bar, beat position and millisecond timing offset
- Browser OfflineAudioContext rendering, so the studio can still humanize audio without a new backend route
- History metadata for groove profile, amount and seed

V4.5 is intentionally non-generative: it changes timing-adjacent gain accents on existing audio and does not synthesize new notes, instruments or voices. The timing map is a controlled heuristic rather than MIDI transcription.

### API

- `POST /rhythm-arrangement/analyze` — analyze the V4.3 beat grid and snap sections to bars when the matching server route is available
- `POST /rhythm-arrangement` — render beat/bar-synced four-stem automation when the matching server route is available
- `POST /instrument-arrangement/analyze` — prepare four Demucs stems and inspect drums/bass/other energy
- `POST /instrument-arrangement` — render vocals + drums + bass + other
- `POST /beat/analyze` — optional server-side V4.3 BPM/beat analysis
- `POST /stem-arrangement/analyze` — inspect vocal/instrumental energy
- `POST /stem-arrangement` — render the V4.1 stem-aware arrangement
- `POST /arrangement/analyze` — inspect energy and heuristic sections
- `POST /arrangement` — build the smart-arranged WAV + MP3

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key. Analytical rhythm/section results should be reviewed before publishing.
