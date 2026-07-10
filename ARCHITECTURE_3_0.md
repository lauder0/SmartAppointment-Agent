# Smart Appointment Agent 3.0 Architecture

3.0 uses a Supervisor + Specialist Agents architecture.

## Goals

- Support natural topic switching across consultation, availability, booking, and recommendation.
- Keep long-running task state explicit instead of mixing all fields into one flat workflow.
- Move domain workflow ownership into specialist agents.
- Preserve stable business behavior while making agent boundaries clear and testable.

## Runtime Flow

1. API receives a user message and loads the session state.
2. `supervisor_entry` normalizes the state and initializes substate containers.
3. `supervisor_router` classifies the next action and selects a specialist.
4. The selected specialist agent handles the domain step:
   - `consultation_subgraph`
   - `availability_subgraph`
   - `booking_subgraph`
   - `recommendation_subgraph`
   - `fallback_subgraph`
5. The specialist writes back its owned substate plus structured result metadata.
6. API persists the updated supervisor state and returns the final assistant response.

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

### Recommendation Agent

- Owns recommendation state.
- Exposes a preference-recall boundary in `memory.py`.
- Currently conservative: it prepares recommendation state without proactively taking over normal chat until recommendation routes are expanded.

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

## Evaluation

3.0 includes:

- `tests/contract/supervisor/test_supervisor_contracts.py`
- `tests/evaluation/cases/supervisor_state_contract_cases.json`
- `tests/evaluation/cases/state_contract_cases.json`

These verify routing, active agent selection, specialist state ownership, context preservation, availability handoff, booking confirmation guard, and intent switching during pending bookings.
