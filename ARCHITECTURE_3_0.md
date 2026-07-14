# Smart Appointment Agent 3.0 Architecture

3.0 uses a Supervisor + Specialist Agents architecture.

## Goals

- Support natural topic switching across consultation, availability, booking, and recommendation.
- Keep long-running task state explicit instead of mixing all fields into one flat workflow.
- Move domain workflow ownership into specialist agents.
- Preserve stable business behavior while making agent boundaries clear and testable.

## Runtime Flow

1. API receives a user message and loads the session state.
2. `api.graph_chat_handler` locks the session, appends the latest `HumanMessage`, and invokes the compiled supervisor graph.
3. `supervisor_entry` normalizes the state and initializes substate containers.
4. `supervisor_router` classifies the next action and selects a specialist.
5. The selected specialist agent handles the domain step:
   - `consultation_subgraph`
   - `availability_subgraph`
   - `booking_subgraph`
   - `recommendation_subgraph`
   - `fallback_subgraph`
6. If availability was gathered to prepare a recommendation and candidate options exist, the graph continues from `availability_subgraph` to `recommendation_subgraph`; otherwise specialist nodes end the turn.
7. The specialist writes back its owned substate plus structured result metadata.
8. API persists the updated supervisor state and returns `final_response` as a streaming text response.

## State Model

- `active_agent`: current specialist responsible for the next step.
- `active_task`: current task label used for observability.
- `task_stack`: reserved for future nested task handling.
- `shared_focus_context`: cross-agent focus such as service, technician, time window, duration, and source action.
- `consultation`: consultation substate.
- `availability`: availability query result and candidate slots.
- `booking`: booking transaction draft, confirmation, guard, and result state.
- `recommendation`: recommendation substate and preference-recall boundary.
- `route_decision`: supervisor routing decision.
- `handoff_payload`: compact payload passed between specialists.
- `last_agent_result`: latest specialist result metadata.
- `last_completed_booking`: latest successful booking result snapshot.
- `final_response`: response text returned to the Web/API streaming boundary.
- `tool_results`: structured trace of router, lookup, recommendation, guard, create, and related service results.

## Session Persistence

Conversation state is stored behind `services.session_state_store.SessionStateStore`.

- `MemorySessionStateStore` is the default for local development and tests.
- `RedisSessionStateStore` is selected with `SESSION_BACKEND=redis` and uses `REDIS_URL`.
- Stored messages are serialized through LangChain message serializers, so the persisted JSON can be restored into graph-ready message objects.
- Each user turn is guarded by a per-session async lock to avoid concurrent mutation of the same conversation state.

## Specialist Internal Design

Each core specialist now owns its own package:

```text
specialists/
  consultation/
    state.py
    actions.py
    response_generator.py
    nodes.py
    graph.py
  availability/
    state.py
    actions.py
    nodes.py
    graph.py
  booking/
    state.py
    nodes.py
    flow.py
    graph.py
    actions.py
    behavior_actions.py
    parser.py
    message_builder.py
  recommendation/
    state.py
    memory.py
    nodes.py
    graph.py
```

### Consultation Agent

- Owns consultation substate.
- Calls consultation tools and response-generation actions internally.
- Returns `consultation.last_answer`, retrieved docs, and `last_agent_result`.

### Availability Agent

- Owns availability criteria, options, available technician names, and answer text.
- Calls realtime schedule tools and availability actions internally.
- Can suggest a handoff to Booking Agent when options are ready.
- When the router reason is `prepare_candidates_for_recommendation` and options exist, the supervisor routes directly into Recommendation Agent after availability completes.

### Booking Agent

- Owns the booking transaction state machine.
- Internal flow:

```text
parse_slots
  -> ask_missing_slots | match_slot
  -> ask_confirmation | fail_booking
  -> interpret_confirmation
  -> guard_booking
  -> create_transaction
  -> record_behavior
  -> complete_booking
```

Additional entry actions:

- `select_recommended_technician` accepts the current recommendation, seeds the booking draft, and asks for confirmation or missing booking fields.
- `cancel_booking` and unclear confirmation responses are handled without bypassing the confirmation guard.

### Recommendation Agent

- Owns recommendation state.
- Exposes a preference-recall boundary in `memory.py`.
- Ranks only verified availability candidates from `availability.options`.
- Supports replacement by excluding the current selected technician before ranking again.
- Returns structured recommendation metadata and a handoff hint to Booking when a user accepts the selected recommendation.
- Remains conservative: it does not proactively take over unrelated chat without a recommendation route.

## Router Actions

The supervisor router emits one action from this set:

- `answer_knowledge`
- `query_availability`
- `start_or_continue_booking`
- `modify_booking`
- `confirm_booking`
- `cancel_booking`
- `generate_recommendation`
- `replace_recommendation`
- `select_recommended_technician`
- `ask_clarification`
- `unsupported`

Routing is deliberately conservative around side effects. Booking creation only happens after Booking has an awaiting-confirmation state, receives positive confirmation, passes the booking guard, and then calls the transaction creation action.

## Intent Understanding And Task Modeling

3.0 now separates user understanding from graph routing. The Supervisor Router is a thin adapter over `agents/understanding`, which produces both a graph-compatible `route_decision` and a persistent `task_frame`.

```text
Input Normalizer
  -> Rule Signal Collector
  -> Context Resolver
  -> Task Modeler
  -> LLM Planner Fallback
  -> Decision Arbiter
```

Important behavior:

- Rule handling collects multiple signals first, instead of routing on the first matched rule.
- Composite intents such as service selection plus technician recommendation become `recommendation_before_booking`.
- Context-dependent confirmations are resolved against current state, so a pending booking confirmation remains guarded.
- `task_frame` tracks task type, primary intent, secondary intents, collected slots, missing slots, subtasks, conflicts, invalidations, safety flags, risk level, and next action.
- `route_decision` keeps the existing graph action contract while carrying richer task metadata for observability and evals.

## Business Action Organization

The supervisor delegates to specialist agents, and each specialist owns its internal control flow.

Stable business actions are organized by ownership:

- `agents/specialists/booking`: booking parsing, draft updates, matching decisions, guard checks, and transaction-facing actions.
- `agents/specialists/availability`: availability parsing and realtime schedule lookup actions.
- `agents/specialists/consultation`: consultation retrieval and response generation.
- `agents/specialists/fallback_actions.py`: clarification, greeting, courtesy, and unsupported-intent responses.
- `agents/supervisor`: routing, handoff, and supervisor graph construction.
- `agents/shared`: shared state adapters, rules, node utilities, and response composition.
- `tools`: stable callable wrappers over service/business operations, retained so the system can evolve toward LLM tool calling without rewriting service access.

The architectural improvement is that each specialist owns its internal workflow and state transitions directly instead of delegating through an extra business-node package.

## Web And API Surface

- `app.py` creates the FastAPI app, registers API routers, registers web routes, mounts `/static`, and initializes knowledge, technician, service catalog, and recommendation scheduler services on startup.
- `web/routes.py` exposes `/`, `/chat`, `/chat/stream`, `/chat/reset`, `/knowledge`, `/technician`, `/technician_schedule`, and user behavior pages.
- `api/chat_handler.py` is a compatibility wrapper over the graph-backed chat handler.
- `api/graph_chat_handler.py` is the actual 3.0 supervisor workflow boundary.

## Run Modes

From the `3.0` directory:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

For direct script execution:

```powershell
python app.py
```

The direct script path starts Uvicorn on `127.0.0.1:8001`; the reload command is preferred for local development.

## Evaluation

3.0 includes:

- `tests/contract/supervisor/test_supervisor_contracts.py`
- `tests/contract/api/test_langgraph_api.py`
- `tests/contract/graph/test_recommendation_flow.py`
- `tests/evaluation/cases/supervisor_state_contract_cases.json`
- `tests/evaluation/cases/state_contract_cases.json`
- `tests/evaluation/cases/conversation_regression_cases.json`
- `tests/evaluation/cases/rag_retrieval_cases.json`

These verify routing, active agent selection, specialist state ownership, context preservation, availability handoff, booking confirmation guard, and intent switching during pending bookings.
