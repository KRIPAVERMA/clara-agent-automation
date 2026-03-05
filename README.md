# Clara Agent Automation
Automated pipeline that converts demo call recordings and onboarding transcripts into
fully-configured **Retell AI agent specifications** for trades businesses such as
electrical, HVAC, plumbing, and property management companies.
---
## Project Overview
Clara AI builds voice AI agents for trades businesses. This pipeline automates the
following workflow:
1. **Transcribe** — Convert onboarding audio/video to text using local Whisper
2. **Extract** — Parse demo call transcripts into structured account memos (JSON)
3. **Generate v1 Agent** — Build initial agent spec from the account memo
4. **Update** — Merge onboarding transcript updates into the account memo (v2)
5. **Generate v2 Agent** — Rebuild the agent spec with updated configuration
No paid APIs are required. OpenAI Whisper runs entirely offline.
---
## Architecture
```
dataset/
  demo_calls/           <- Demo call transcripts (.txt) + videos (.mp4)
  onboarding_calls/     <- Onboarding audio (.m4a, .mp4) + transcripts (.txt)
scripts/
  transcribe_onboarding.py   <- Step 1: Whisper transcription of onboarding media
  extract_account_data.py    <- Step 2: Extract JSON memos from demo transcripts
  generate_agent_spec.py     <- Step 3: Build v1_agent_spec.json
  apply_onboarding_update.py <- Step 4: Merge onboarding updates -> v2 memo + changelog
  generate_agent_v2.py       <- Step 5: Build v2_agent_spec.json
  run_all.py                 <- Master pipeline (runs all 5 steps)
  extract_demo.py            <- Regex-based field extraction from transcripts
  generate_agent.py          <- Shared agent spec builder
  onboarding_update.py       <- Merge logic and account matching
  transcribe_videos.py       <- Whisper transcription for demo videos
utils/
  file_utils.py              <- load/save transcript, JSON, text helpers
  version_utils.py           <- versioned path helpers, changelog generator
templates/
  agent_prompt_template.txt  <- System prompt template with {placeholders}
outputs/
  accounts/
    {account_id}/
      v1_account_memo.json   <- Extracted account data (v1)
      v1_agent_spec.json     <- Generated agent config (v1)
      v2_account_memo.json   <- Updated account data after onboarding (v2)
      v2_agent_spec.json     <- Regenerated agent config (v2)
      changes.md             <- Field-level changelog v1 -> v2
```
---
## Requirements
| Requirement | Notes |
|---|---|
| Python 3.10 | Required for torch / Whisper (3.14 not yet supported by torch) |
| openai-whisper | Local speech-to-text |
| torch | Required by Whisper |
| ffmpeg | Must be on PATH — https://ffmpeg.org/download.html |
Install Python dependencies:
```bash
py -3.10 -m pip install openai-whisper torch ffmpeg-python
```
---
## How to Run
### Full pipeline (all 5 steps)
```bash
python scripts/run_all.py
```
Runs every step automatically and prints a summary of all generated outputs.
---
### Individual Steps
**Step 1 — Transcribe onboarding audio/video**
```bash
py -3.10 scripts/transcribe_onboarding.py
```
Transcribes `.mp4` / `.m4a` files in `dataset/onboarding_calls/` to `.txt`.
**Step 2 — Extract account data from demo transcripts**
```bash
py scripts/extract_account_data.py
```
Reads `dataset/demo_calls/*.txt` and writes `v1_account_memo.json` per account.
**Step 3 — Generate v1 agent spec**
```bash
py scripts/generate_agent_spec.py
```
Reads `v1_account_memo.json` and writes `v1_agent_spec.json`.
**Step 4 — Apply onboarding updates**
```bash
py scripts/apply_onboarding_update.py
```
Merges onboarding transcript data into accounts -> `v2_account_memo.json` + `changes.md`.
**Step 5 — Generate v2 agent spec**
```bash
py scripts/generate_agent_v2.py
```
Reads `v2_account_memo.json` and writes `v2_agent_spec.json`.
---
## Expected Output Structure
```
outputs/accounts/
  greenleaf_6555c4/
    v1_account_memo.json
    v1_agent_spec.json
    v2_account_memo.json
    v2_agent_spec.json
    changes.md
  sunrise_e42b03/
    v1_account_memo.json
    v1_agent_spec.json
```
---
## Notes
- Whisper base model (~139 MB) downloaded automatically on first run, cached at `~/.cache/whisper/`
- CPU transcription: ~1 min per minute of audio
- Account IDs are deterministic MD5 hashes of the company name
- Re-running the pipeline regenerates all outputs cleanly
