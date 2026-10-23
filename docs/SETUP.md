# What to download, and when

Download only what the current build phase needs (PRD section 24). Phase A–C runs entirely on your Mac and
costs nothing. The heavy model weights belong on a rented NVIDIA GPU, not on the Mac.

Sizes are approximate; check the linked pages before downloading.

## Step 1 — now: run this repo on your Mac (Phases A–C)

| Install | Why | macOS command |
|---|---|---|
| Xcode Command Line Tools | git, compilers | `xcode-select --install` |
| Homebrew | package manager | see <https://brew.sh> |
| uv | creates the Python environment (installs Python 3.12 for you) | `brew install uv` |
| Node.js 22 LTS | frontend build and dev server | `brew install node@22` |
| A code editor | VS Code, Cursor or similar | optional |

About 1–2 GB in total. SQLite is built into Python, so no database server is needed yet.

```bash
git clone https://github.com/ahmed-farahat-pro/claude-codex-problem-x.git
cd claude-codex-problem-x
git checkout 4weeks

# backend (terminal 1)
cd backend
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/uvicorn app.main:create_app --factory --reload --port 8000

# frontend (terminal 2)
cd frontend
npm install
npm run dev        # open http://localhost:5173
```

This is deterministic mode: real server state, real sessions, Stop, tools, memory and checks, but template
drafts instead of a paid model.

### When you are ready for real model drafts (Phase C)

| Get | Why | How |
|---|---|---|
| Gemini API key | real drafts and tutor reasoning | Google AI Studio → API keys |
| Gemini SDK | server-side client | `cd backend && uv pip install -e ".[gemini]"` |

Put `GEMINI_API_KEY=...` and `FOURWEEKS_MODE=gemini` in `backend/.env` (copy from `.env.example`). Never put the
key in the frontend. The PRD reserves SAR75–187.50 for model API calls during the demo.

### When the lab moves to a real browser (next engineering step)

| Install | Why | How |
|---|---|---|
| Playwright + Chromium | drive and capture the real lab browser | `uv pip install playwright && .venv/bin/playwright install chromium` (~150 MB) |

Use a dedicated browser profile with synthetic data only (PRD section 6).

## Step 2 — recorded lesson production (Phase B)

On the Mac:

| Install | Why | macOS command |
|---|---|---|
| FFmpeg | compose face + screen, captions, exports | `brew install ffmpeg` |
| OBS Studio | deterministic screen capture of the lab run | `brew install --cask obs` |
| A video editor (optional) | DaVinci Resolve (free), iMovie or similar | from the vendor |

On a rented GPU (accounts below), not on the Mac:

| Model | Use | Download | Notes |
|---|---|---|---|
| FLUX.1 schnell | original presenter portrait | `hf download black-forest-labs/FLUX.1-schnell` | Apache 2.0. Tens of GB. You can instead use any image source you own the rights to |
| Wan 2.2 TI2V 5B (optional) | gentle presenter movement | `hf download Wan-AI/Wan2.2-TI2V-5B --local-dir ./Wan2.2-TI2V-5B` | Apache 2.0. Needs ≥24 GB VRAM with offload; 720p at 24 fps |
| Chatterbox Multilingual V3 | Arabic voice | `pip install chatterbox-tts` (weights download on first use) | MIT. Arabic is `language_id="ar"`; load with `t3_model="v3"`. Use an owned or consented voice reference. Can be tried slowly on the Mac |
| MuseTalk 1.5 | lip sync of approved audio onto the base clip | clone the repo, then `sh ./download_weights.sh` | MIT code. NVIDIA only: Python 3.10, PyTorch 2.0.1 + CUDA 11.8, mmcv 2.0.1 / mmdet 3.1.0 / mmpose 1.1.0, FFmpeg. Several GB of weights (musetalkV15, sd-vae, whisper, dwpose, face-parse-bisent, syncnet) |

`hf` comes from `pip install -U "huggingface_hub[cli]"` (older versions call it `huggingface-cli download`).
Keep MuseTalk and Chatterbox in separate Python environments; their dependencies conflict (PRD section 40).

## Step 3 — live tutor (Phase D)

| Install | Where | How | Notes |
|---|---|---|---|
| whisper.cpp + `large-v3-turbo` | Mac (Metal) or GPU box | `git clone https://github.com/ggml-org/whisper.cpp && cd whisper.cpp && cmake -B build && cmake --build build -j --config Release && sh ./models/download-ggml-model.sh large-v3-turbo` | ~1.6 GB model file `ggml-large-v3-turbo.bin` |
| LiveKit server (local dev) | Mac | `brew install livekit` then `livekit-server --dev` | Dev key `devkey`, secret `secret`. Linux: `curl -sSL https://get.livekit.io \| bash` |
| LiveKit CLI | Mac | `brew install livekit-cli` (command `lk`) | room and token testing |
| LiveKit Python SDKs | backend / avatar worker | `pip install livekit-agents livekit-api` | server-side short-lived tokens; custom avatar worker (`AvatarRunner`) |

The streaming avatar adapter (MuseTalk behind a LiveKit avatar worker) is custom code and the largest
uncertainty in the plan. Benchmark it before calling the tutor "live".

## Accounts to create (free to open; pay only when used)

| Account | Needed from | Used for |
|---|---|---|
| Google AI Studio | Phase C | Gemini API key |
| Hugging Face | Phase B | model downloads |
| RunPod (or another GPU host) | Phase B | A6000 at about USD 0.59/h; stop the pod after each test, keep a ~100 GB volume for weights |
| LiveKit Cloud (optional) | Phase D | hosted transport; the local server is enough at first |
| Cloudflare | Phase E | Stream for recorded lessons |
| Discord | Phase E | cohort community |

## Do not download or buy

- A GPU. Rent one and stop it after testing (PRD sections 7 and 30).
- CUDA for the Mac. It does not run there; MuseTalk and Wan need the rented NVIDIA box.
- A managed avatar subscription. The plan uses your own character and pipeline.
- Any real customer or learner data for the labs. Fixtures are synthetic on purpose.
