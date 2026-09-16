# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V4.6 — Story → Lyrics → Music → 4 Stems → Vocal Enhance → Mix → Smart Arrange → Structure → Section-Aware Arrangement → Stem-Aware Arrangement → Instrument Stem Intelligence → Beat & Tempo Intelligence → Rhythm-Aware Arrangement → Groove & Humanization → Melody & Chord Intelligence → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

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
- **Melody & Chord Intelligence V4.6:** estimated key/mode, chord-template timeline, harmonic density, chord-change rate and tension indicators from existing audio
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support and karaoke highlighting
- **Lyric synchronization:** faster-whisper ASR with editable timing
- **Audio quality:** loudness, peak, duration and silence inspection
- **Export:** WAV 24-bit / 44.1 kHz and MP3 320 kbps where applicable

### V4.6 harmony controls

- Estimated key and major/minor mode
- Key confidence and chord confidence
- Chord-change timeline with start/end time
- Harmonic density measured as estimated changes per minute
- Tension indicator per harmonic region
- Analyze Harmony, Analyze Chords and Align to Structure actions
- Copy complete harmony JSON for downstream workflows
- Server-side lightweight WAV analyzer when `/harmony/analyze` is available, with browser Web Audio fallback

V4.6 is intentionally analytical rather than generative. The harmonic map is an estimate based on pitch-class/chroma energy and chord templates; lo-fi noise, reverb, layered instruments and bass ambiguity can produce incorrect keys or chords. It is not exact MIDI or symbolic chord transcription.

### API

- `POST /harmony/analyze` — optional server-side V4.6 key/chord/harmonic analysis
- `POST /rhythm-arrangement/analyze` — analyze the V4.3 beat grid and snap sections to bars when the matching server route is available
- `POST /rhythm-arrangement` — render beat/bar-synced four-stem automation when the matching server route is available
- `POST /instrument-arrangement/analyze` — prepare four Demucs stems and inspect drums/bass/other energy
- `POST /instrument-arrangement` — render vocals + drums + bass + other
- `POST /beat/analyze` — optional server-side V4.3 BPM/beat analysis
- `POST /stem-arrangement/analyze` — inspect vocal/instrumental energy
- `POST /stem-arrangement` — render the V4.1 stem-aware arrangement
- `POST /arrangement/analyze` — inspect energy and heuristic sections
- `POST /arrangement` — build the smart-arranged WAV + MP3

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key. Analytical harmonic/rhythm/section results should be reviewed before publishing.
