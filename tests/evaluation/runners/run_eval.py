"""Run the SmartAppointment-Agent conversational evaluation set.

The runner calls the same chat entrypoint used by the web UI. By default it
skips cases marked as side-effecting, because those may create appointments.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

CASE_FILE = Path(__file__).resolve().parents[1] / "cases" / "conversation_regression_cases.json"


@dataclass
class TurnResult:
    turn_index: int
    user: str
    response: str
    passed: bool
    duration_ms: float = 0.0
    failures: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    title: str
    category: str
    tags: list[str]
    passed: bool
    skipped: bool = False
    reason: str | None = None
    duration_ms: float = 0.0
    turns: list[TurnResult] = field(default_factory=list)


def load_cases(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def case_matches(case: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.case and case["id"] not in args.case:
        return False
    if args.category and case.get("category") not in args.category:
        return False
    if args.tag:
        tags = set(case.get("tags", []))
        if not any(tag in tags for tag in args.tag):
            return False
    return True


async def collect_response(user_input: str, session_id: str) -> str:
    from api.chat_handler import ProcessUserInput_stream

    chunks: list[str] = []
    async for chunk in ProcessUserInput_stream(user_input, session_id=session_id):
        chunks.append(chunk)
    return "".join(chunks)


async def get_graph_state(session_id: str) -> dict[str, Any]:
    try:
        from api.graph_chat_handler import get_graph_session_state
    except Exception:
        return {}
    state = await get_graph_session_state(session_id)
    return dict(state) if state else {}


def get_state_path(state: dict[str, Any], path: str) -> Any:
    path = _canonical_state_path(path)
    current: Any = state
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _canonical_state_path(path: str) -> str:
    aliases = {
        "focus_context.": "shared_focus_context.",
        "availability_result.": "availability.",
        "availability.criteria.": "availability_result.criteria_snapshot.",
        "appointment.": "booking.draft.",
    }
    for old, new in aliases.items():
        if path.startswith(old):
            return new + path[len(old):]
    return path


def derived_intent(state: dict[str, Any]) -> str:
    from api.graph_state_view import state_to_intent

    return state_to_intent(state)


def derived_pending_action(state: dict[str, Any]) -> str | None:
    status = (state.get("booking") or {}).get("status")
    if status == "drafting":
        return "collect_appointment_info"
    if status == "awaiting_confirmation":
        return "awaiting_appointment_confirmation"
    return None


def check_expectations(
    response: str,
    state: dict[str, Any],
    expect: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    agent_label = expect.get("agent_label")
    if agent_label and f"[{agent_label}]" not in response:
        failures.append(f"expected agent label [{agent_label}]")

    for text in expect.get("must_include_all", []):
        if text not in response:
            failures.append(f"missing required text: {text}")

    include_any = expect.get("must_include_any", [])
    if include_any and not any(text in response for text in include_any):
        failures.append(f"expected at least one text: {include_any}")

    for text in expect.get("must_not_include_any", []):
        if text in response:
            failures.append(f"unexpected text present: {text}")

    route_action = expect.get("route_action")
    if route_action:
        actual = get_state_path(state, "route_decision.action")
        if actual != route_action:
            failures.append(f"expected route_decision.action={route_action}, got {actual}")

    booking_status = expect.get("booking_status")
    if booking_status:
        actual = get_state_path(state, "booking.status")
        if actual != booking_status:
            failures.append(f"expected booking.status={booking_status}, got {actual}")

    state_intent = expect.get("state_intent")
    if state_intent and derived_intent(state) != state_intent:
        failures.append(f"expected derived state.intent={state_intent}, got {derived_intent(state)}")

    pending_action = expect.get("state_pending_action")
    if pending_action and derived_pending_action(state) != pending_action:
        failures.append(
            f"expected derived state.pending_action={pending_action}, "
            f"got {derived_pending_action(state)}"
        )

    for path, expected in expect.get("state_equals", {}).items():
        actual = get_state_path(state, path)
        if actual != expected:
            failures.append(f"expected state.{path}={expected}, got {actual}")

    for path, expected_text in expect.get("state_contains", {}).items():
        actual = get_state_path(state, path)
        if expected_text not in str(actual):
            failures.append(f"expected state.{path} to contain {expected_text}, got {actual}")

    for path, unexpected in expect.get("state_not_equals", {}).items():
        actual = get_state_path(state, path)
        if actual == unexpected:
            failures.append(f"expected state.{path} not to equal {unexpected}")

    for path, min_length in expect.get("state_list_min_length", {}).items():
        actual = get_state_path(state, path)
        if not isinstance(actual, list):
            failures.append(f"expected state.{path} to be a list, got {actual}")
        elif len(actual) < min_length:
            failures.append(f"expected state.{path} length >= {min_length}, got {len(actual)}")

    for path in expect.get("state_path_exists", []):
        actual = get_state_path(state, path)
        if actual is None:
            failures.append(f"expected state.{path} to exist")

    return failures


async def run_case(case: dict[str, Any], args: argparse.Namespace) -> CaseResult:
    if case.get("side_effect") and not args.include_side_effects:
        return CaseResult(
            case_id=case["id"],
            title=case["title"],
            category=case.get("category", "-"),
            tags=case.get("tags", []),
            passed=True,
            skipped=True,
            reason="side-effecting case skipped",
        )

    from api.chat_handler import reset_session

    session_id = f"eval-{case['id']}-{uuid.uuid4().hex[:8]}"
    await reset_session(session_id)
    result = CaseResult(
        case_id=case["id"],
        title=case["title"],
        category=case.get("category", "-"),
        tags=case.get("tags", []),
        passed=True,
    )
    case_start = time.perf_counter()

    for index, turn in enumerate(case["turns"], start=1):
        turn_start = time.perf_counter()
        response = await collect_response(turn["user"], session_id)
        duration_ms = (time.perf_counter() - turn_start) * 1000
        state = await get_graph_state(session_id)
        failures = check_expectations(response, state, turn.get("expect", {}))
        turn_result = TurnResult(
            turn_index=index,
            user=turn["user"],
            response=response,
            passed=not failures,
            duration_ms=duration_ms,
            failures=failures,
        )
        result.turns.append(turn_result)
        if failures:
            result.passed = False
            if args.fail_fast:
                break

    result.duration_ms = (time.perf_counter() - case_start) * 1000
    return result


def print_case_list(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        side_effect = " side-effect" if case.get("side_effect") else ""
        print(
            f"{case['id']:<6} {case.get('category', '-'):<18} "
            f"turns={len(case.get('turns', [])):<2} {case['title']}{side_effect}"
        )


def print_result(result: CaseResult, show_responses: bool) -> None:
    if result.skipped:
        print(f"SKIP {result.case_id} {result.title} ({result.reason})")
        return

    status = "PASS" if result.passed else "FAIL"
    print(f"{status} {result.case_id} {result.title}")

    for turn in result.turns:
        turn_status = "ok" if turn.passed else "bad"
        print(f"  T{turn.turn_index} {turn_status} ({turn.duration_ms:.0f} ms): {turn.user}")
        if show_responses or not turn.passed:
            print(f"    response: {turn.response}")
        for failure in turn.failures:
            print(f"    - {failure}")


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percent)))
    return ordered[index]


def print_metric_table(title: str, rows: list[tuple[str, int, int]]) -> None:
    if not rows:
        return
    print(f"\n{title}:")
    for name, passed, total in rows:
        rate = (passed / total * 100) if total else 0
        print(f"  {name:<28} {passed:>3}/{total:<3} {rate:>5.1f}%")


def print_metrics(results: list[CaseResult]) -> None:
    executed = [result for result in results if not result.skipped]
    turns = [turn for result in executed for turn in result.turns]
    passed_cases = sum(1 for result in executed if result.passed)
    passed_turns = sum(1 for turn in turns if turn.passed)
    case_total = len(executed)
    turn_total = len(turns)
    case_rate = (passed_cases / case_total * 100) if case_total else 0
    turn_rate = (passed_turns / turn_total * 100) if turn_total else 0
    durations = [turn.duration_ms for turn in turns]

    print("\nMetrics:")
    print(f"  case_pass_rate          {passed_cases}/{case_total} {case_rate:.1f}%")
    print(f"  turn_pass_rate          {passed_turns}/{turn_total} {turn_rate:.1f}%")
    if durations:
        print(f"  avg_turn_latency_ms     {sum(durations) / len(durations):.0f}")
        print(f"  p95_turn_latency_ms     {percentile(durations, 0.95):.0f}")

    category_totals: dict[str, list[int]] = {}
    tag_totals: dict[str, list[int]] = {}
    for result in executed:
        category = result.category
        category_totals.setdefault(category, [0, 0])
        category_totals[category][1] += 1
        category_totals[category][0] += 1 if result.passed else 0
        for tag in result.tags:
            tag_totals.setdefault(tag, [0, 0])
            tag_totals[tag][1] += 1
            tag_totals[tag][0] += 1 if result.passed else 0

    category_rows = sorted(
        ((name, counts[0], counts[1]) for name, counts in category_totals.items()),
        key=lambda row: row[0],
    )
    print_metric_table("By category", category_rows)

    important_tags = [
        "multi_turn",
        "availability",
        "appointment",
        "knowledge",
        "context_resume",
        "confirmation_guard",
        "preference",
        "intent_switch",
        "service_selection",
        "robustness",
    ]
    tag_rows = [
        (tag, tag_totals[tag][0], tag_totals[tag][1])
        for tag in important_tags
        if tag in tag_totals
    ]
    print_metric_table("By key tag", tag_rows)

    slow_turns = sorted(
        (
            (turn.duration_ms, result.case_id, turn.turn_index, turn.user[:42])
            for result in executed
            for turn in result.turns
        ),
        reverse=True,
    )[:5]
    if slow_turns:
        print("\nSlowest turns:")
        for duration_ms, case_id, turn_index, user in slow_turns:
            print(f"  {duration_ms:>7.0f} ms  {case_id} T{turn_index}: {user}")


def write_json_report(path: Path, results: list[CaseResult]) -> None:
    payload = {
        "results": [
            {
                "case_id": result.case_id,
                "title": result.title,
                "category": result.category,
                "tags": result.tags,
                "passed": result.passed,
                "skipped": result.skipped,
                "reason": result.reason,
                "duration_ms": result.duration_ms,
                "turns": [
                    {
                        "turn_index": turn.turn_index,
                        "user": turn.user,
                        "passed": turn.passed,
                        "duration_ms": turn.duration_ms,
                        "failures": turn.failures,
                    }
                    for turn in result.turns
                ],
            }
            for result in results
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run conversational eval cases.")
    parser.add_argument("--cases-file", type=Path, default=CASE_FILE)
    parser.add_argument("--list", action="store_true", help="List cases and exit.")
    parser.add_argument("--case", action="append", help="Run one case id. Repeatable.")
    parser.add_argument("--category", action="append", help="Run one category. Repeatable.")
    parser.add_argument("--tag", action="append", help="Run cases matching a tag. Repeatable.")
    parser.add_argument(
        "--include-side-effects",
        action="store_true",
        help="Also run cases that may create appointments.",
    )
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--show-responses", action="store_true")
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    args = parser.parse_args()

    data = load_cases(args.cases_file)
    cases = [case for case in data["cases"] if case_matches(case, args)]

    if args.list:
        print_case_list(cases)
        return 0

    if not cases:
        print("No cases selected.")
        return 1

    results: list[CaseResult] = []
    for case in cases:
        result = await run_case(case, args)
        results.append(result)
        print_result(result, args.show_responses)
        if args.fail_fast and not result.passed:
            break

    total = len(results)
    skipped = sum(1 for result in results if result.skipped)
    failed = sum(1 for result in results if not result.passed and not result.skipped)
    passed = total - skipped - failed
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped, {total} selected.")
    print_metrics(results)
    if args.json_report:
        write_json_report(args.json_report, results)
        print(f"\nJSON report written to {args.json_report}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
