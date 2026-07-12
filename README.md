# Smart Appointment AI Agent 3.0

3.0 uses a **Supervisor + Specialist Agents** architecture. The supervisor owns intent routing and cross-agent handoff. Consultation, availability, booking, recommendation, and fallback each expose a graph entrypoint; the richer booking workflow is implemented as an internal deterministic flow over booking nodes.

## Architecture

```text
User
  -> Web/API Chat
  -> Session State Store (memory by default, Redis optional)
  -> Supervisor Graph
      -> Consultation Agent
      -> Availability Agent
          -> Recommendation Agent (only when availability was gathered for recommendation)
      -> Booking Agent
      -> Recommendation Agent
      -> Fallback Handler
  -> Response
```

## Core Ideas

- `Supervisor`: routes user intent, owns cross-agent handoff, and tracks active agent/task.
- `Consultation Agent`: answers services, prices, address, business hours, policies, and other knowledge questions.
- `Availability Agent`: parses schedule constraints, returns realtime available technician options, and can feed those candidates into recommendation.
- `Booking Agent`: owns booking draft, slot filling, matching, recommendation acceptance, confirmation, guard, creation, behavior recording, and completion.
- `Recommendation Agent`: ranks verified available technicians, supports "change another one", and hands accepted recommendations back to Booking.
- `Fallback Handler`: handles clarification, greeting, courtesy, and unsupported requests.

## State Model

3.0 uses `SupervisorState`:

```text
SupervisorState
  - session_id / user_id / messages
  - active_agent / active_task / task_stack
  - shared_focus_context
  - consultation
  - availability
  - booking
  - recommendation
  - route_decision
  - handoff_payload
  - last_agent_result
  - last_completed_booking
  - final_response / error
  - tool_results
```

Important ownership rules:

- `shared_focus_context`: cross-agent facts such as service type, time, duration, gender preference, technician, and style preference.
- `consultation`: private consultation state.
- `availability`: private availability state, including query criteria, candidate options, available technician names, and answer text.
- `booking`: private transaction state. Only Booking Agent can progress toward guarded appointment creation.
- `recommendation`: private recommendation state, preference-recall boundary, ranked candidates, selected recommendation, alternatives, confidence, and excluded technician IDs.

## Runtime Details

- Web routes call `api.chat_handler.ProcessUserInput_stream`, which delegates to the 3.0 supervisor workflow in `api.graph_chat_handler`.
- A session is loaded, locked, updated with the latest `HumanMessage`, passed through the compiled LangGraph supervisor, then persisted.
- `SESSION_BACKEND=memory` is the default local session store. `SESSION_BACKEND=redis` enables Redis-backed state with `REDIS_URL`, TTL, key prefix, and lock timeout environment variables.
- `/chat` and `/chat/stream` both return streaming text responses. `/chat/reset` clears one stored session.
- The FastAPI app registers API routers for appointment, consultation, task, knowledge, technician, and user behavior pages/APIs, plus the web UI routes.

## Specialist Agent Layout

```text
agents/
  supervisor/
    graph_builder.py
    nodes.py
    router_actions.py
    routing.py
    state.py
  shared/
    state.py
    node_utils.py
    response_composer.py
    context/
      rules.py
  specialists/
    consultation/
      actions.py
      graph.py
      nodes.py
      response_generator.py
      state.py
    availability/
      actions.py
      graph.py
      nodes.py
      state.py
    booking/
      actions.py
      behavior_actions.py
      graph.py
      flow.py
      message_builder.py
      nodes.py
      parser.py
      state.py
    recommendation/
      graph.py
      memory.py
      nodes.py
      state.py
    fallback.py
    fallback_actions.py
    common.py
tools/
services/
db/
tests/
```

The 3.0 specialist agents now own their domain actions directly. Parsing, response generation, availability lookup, recommendation ranking, booking guards, and routing helpers live inside the relevant agent package, while `tools/` remains the stable callable boundary over business services. This keeps the graph readable today and leaves a clear path to future tool-calling agents.

## Run

```powershell
cd 3.0
Copy-Item .env.example .env
# Fill in the required API keys in .env

pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Running `python app.py` starts Uvicorn on `127.0.0.1:8001`; the README command above uses port `8000` for reload-friendly local development.

The local `.env`, SQLite database, Python caches, and generated evaluation
reports are ignored by Git. Do not commit real API keys. If a key has ever been
shared or committed, revoke it before publishing the repository.

## Test And Evaluation

```powershell
python -m pytest tests\contract\supervisor -q
python -m pytest tests\unit tests\contract -q
python tests\evaluation\runners\run_eval.py --cases-file tests\evaluation\cases\supervisor_state_contract_cases.json
python tests\evaluation\runners\run_eval.py
python tests\evaluation\runners\run_rag_retrieval_eval.py --cases-file tests\evaluation\cases\rag_retrieval_cases.json
```

## Current Boundaries

- The outer architecture is a true supervisor plus specialist-agent boundary.
- Each business specialist now has its own state/nodes/graph package.
- Stable business actions are now organized inside the owning agent package to preserve tested parsing, RAG, availability, matching, guard, and write behavior without an extra business-node layer.
- Availability can flow directly into recommendation when the router labels the request as `prepare_candidates_for_recommendation` and candidate options exist.
- Recommendation acceptance routes through `select_recommended_technician` into Booking rather than creating appointments itself.
- `tools/` wraps service calls and reusable business operations so future LLM tool-calling can reuse the same interface.
- Recommendation is active for user-requested ranking/replacement over verified availability candidates, but it still does not proactively take over unrelated chat.
