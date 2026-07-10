# Test Suite

The 3.0 test suite is organized by system layer:

```text
tests/
  unit/                 # DB, service, tool, and session-level tests
  contract/
    api/                # API boundary contracts
    graph/              # Reused business-node contracts
    supervisor/         # 3.0 Supervisor route/state contracts
  e2e/                  # Multi-turn user-flow tests
  evaluation/           # Conversational and retrieval evaluation sets
```

## Common Commands

Run the 3.0 supervisor contracts:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\supervisor
```

Run the fast unit and contract suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit tests\contract
```

Run all pytest-discovered tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Run the 3.0 supervisor state evaluation:

```powershell
.\.venv\Scripts\python.exe tests\evaluation\runners\run_eval.py --cases-file tests\evaluation\cases\supervisor_state_contract_cases.json
```

Run broader conversational evaluation cases:

```powershell
.\.venv\Scripts\python.exe tests\evaluation\runners\run_eval.py
```

Run retrieval evaluation cases:

```powershell
.\.venv\Scripts\python.exe tests\evaluation\runners\run_rag_retrieval_eval.py --cases-file tests\evaluation\cases\rag_retrieval_cases.json
```

## 3.0 Evaluation Focus

- Supervisor route decision: consultation, availability, booking, fallback.
- Specialist boundary: each subgraph owns its private state and returns a structured `last_agent_result`.
- Shared state: `shared_focus_context` persists cross-subgraph facts.
- Booking safety: write-side behavior remains guarded by booking confirmation and guard checks.
