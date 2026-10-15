# Prerequisites & example local setup

Install: Cursor editor, Git, Python 3.11+, Node.js LTS and npm, browser with modern JavaScript support. Optional: Docker Desktop/Engine with Compose. Do not configure LLM or Cisco API credentials for synthetic demo.

## Check versions
```bash
python3 --version
node --version
npm --version
git --version
docker compose version # optional
```

## Inspect and test original runtime (before refactor)
```bash
cd reference_projects/agent_runtime
python3 compiler.py
python3 -m unittest discover -s tests -v
python3 server.py
# Open http://127.0.0.1:8876 ; confirm actual port from server source/env
```

## Proposed local developer workflow (Cursor creates in phase 1)
```bash
# from project root after Cursor has implemented the target apps
python3 -m venv .venv
source .venv/bin/activate    # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r apps/api/requirements.txt
cd apps/web && npm install && npm run dev
# in another terminal: python apps/api/main.py, or equivalent documented command
```
No `apps/` implementation is shipped in this handoff yet. Commands are illustrative future targets and must be adjusted to the actual code and tested. Use pinned dependency versions and safe package sources.

## Credentials / permissions staged
- Stage 1: none; localhost and synthetic only.
- Stage 2: optional LLM provider key, behind opt-in and strict read/reason bounds. Keep it in `.env`, excluded from Git.
- Stage 3: local agent identity/certs for cross-process A2A; AGNTCY Directory/SLIM only after successful compatibility assessment.
- Stage 4: customer sponsor, read-only data entitlements, named IT/OT owners, data processing controls, metric owner, evidence capture and policy sign-off.

## Security check
Never grant Cursor or the application write permission to OT systems. Do not paste real keys, private customer telemetry, HR/occupancy PII or Cisco secrets into prompts, model logs, test fixtures or source control.
