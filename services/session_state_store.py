"""Session state persistence for 3.0 supervisor conversations."""

from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional, Protocol

from dotenv import load_dotenv
from langchain_core.messages import messages_from_dict, messages_to_dict

load_dotenv()


DEFAULT_SESSION_TTL_SECONDS = 60 * 60 * 2
DEFAULT_SESSION_KEY_PREFIX = "smart_appointment:session"
SupervisorState = Dict[str, Any]


class SessionStateStore(Protocol):
    """Persistence boundary for graph session state."""

    async def get(self, session_id: str) -> Optional[SupervisorState]:
        ...

    async def set(self, session_id: str, state: SupervisorState) -> None:
        ...

    async def delete(self, session_id: str) -> None:
        ...

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncIterator[None]:
        yield


def _json_default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def serialize_supervisor_state(state: SupervisorState) -> Dict[str, Any]:
    """Convert a SupervisorState into a JSON-compatible dictionary."""
    serialized = dict(state)
    serialized["messages"] = messages_to_dict(list(state.get("messages") or []))
    return serialized


def deserialize_supervisor_state(payload: Dict[str, Any]) -> SupervisorState:
    """Restore a SupervisorState from a JSON-compatible dictionary."""
    state = dict(payload)
    state["messages"] = messages_from_dict(state.get("messages") or [])
    return state  # type: ignore[return-value]


serialize_agent_state = serialize_supervisor_state
deserialize_agent_state = deserialize_supervisor_state


def _round_trip_state(state: SupervisorState) -> SupervisorState:
    """Deep-copy state through JSON serialization to avoid shared mutation."""
    payload = json.loads(json.dumps(serialize_supervisor_state(state), ensure_ascii=False, default=_json_default))
    return deserialize_supervisor_state(payload)


class MemorySessionStateStore:
    """In-process fallback store for local development and tests."""

    def __init__(self, ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._states: Dict[str, Dict[str, Any]] = {}
        self._expires_at: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get(self, session_id: str) -> Optional[SupervisorState]:
        expires_at = self._expires_at.get(session_id)
        if expires_at is not None and expires_at <= time.time():
            await self.delete(session_id)
            return None
        payload = self._states.get(session_id)
        if payload is None:
            return None
        return deserialize_supervisor_state(json.loads(json.dumps(payload, ensure_ascii=False, default=_json_default)))

    async def set(self, session_id: str, state: SupervisorState) -> None:
        self._states[session_id] = serialize_supervisor_state(_round_trip_state(state))
        self._expires_at[session_id] = time.time() + self.ttl_seconds

    async def delete(self, session_id: str) -> None:
        self._states.pop(session_id, None)
        self._expires_at.pop(session_id, None)

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncIterator[None]:
        lock = self._locks.setdefault(session_id, asyncio.Lock())
        async with lock:
            yield


class RedisSessionStateStore:
    """Redis-backed store shared by multiple application workers."""

    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        key_prefix: str = DEFAULT_SESSION_KEY_PREFIX,
        lock_timeout_seconds: int = 30,
        lock_blocking_timeout_seconds: int = 5,
    ):
        try:
            import redis.asyncio as redis
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional deployment dependency
            raise RuntimeError("Redis session backend requires redis>=5.0.0") from exc

        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix.rstrip(":")
        self.lock_timeout_seconds = lock_timeout_seconds
        self.lock_blocking_timeout_seconds = lock_blocking_timeout_seconds

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{session_id}"

    def _lock_key(self, session_id: str) -> str:
        return f"{self.key_prefix}:lock:{session_id}"

    async def get(self, session_id: str) -> Optional[SupervisorState]:
        raw = await self.redis.get(self._key(session_id))
        if not raw:
            return None
        return deserialize_supervisor_state(json.loads(raw))

    async def set(self, session_id: str, state: SupervisorState) -> None:
        payload = json.dumps(serialize_supervisor_state(state), ensure_ascii=False, default=_json_default)
        await self.redis.set(self._key(session_id), payload, ex=self.ttl_seconds)

    async def delete(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncIterator[None]:
        lock = self.redis.lock(
            self._lock_key(session_id),
            timeout=self.lock_timeout_seconds,
            blocking_timeout=self.lock_blocking_timeout_seconds,
        )
        acquired = await lock.acquire()
        if not acquired:
            raise TimeoutError(f"Timed out waiting for session lock: {session_id}")
        try:
            yield
        finally:
            await lock.release()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def create_session_state_store() -> SessionStateStore:
    """Create the configured session state store."""
    backend = (os.getenv("SESSION_BACKEND") or "memory").strip().lower()
    ttl_seconds = _env_int("SESSION_TTL_SECONDS", DEFAULT_SESSION_TTL_SECONDS)

    if backend == "redis":
        redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
        key_prefix = os.getenv("SESSION_KEY_PREFIX") or DEFAULT_SESSION_KEY_PREFIX
        return RedisSessionStateStore(
            redis_url=redis_url,
            ttl_seconds=ttl_seconds,
            key_prefix=key_prefix,
            lock_timeout_seconds=_env_int("SESSION_LOCK_TIMEOUT_SECONDS", 30),
            lock_blocking_timeout_seconds=_env_int("SESSION_LOCK_BLOCKING_TIMEOUT_SECONDS", 5),
        )

    if backend == "memory":
        return MemorySessionStateStore(ttl_seconds=ttl_seconds)

    raise ValueError("SESSION_BACKEND must be 'memory' or 'redis'")
