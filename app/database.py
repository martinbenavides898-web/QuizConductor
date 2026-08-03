from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
import unicodedata
import uuid
from functools import lru_cache
from typing import Any, Callable, TypeVar

import streamlit as st
from supabase import Client, create_client
from supabase.client import ClientOptions


T = TypeVar("T")
PBKDF2_ITERATIONS = 310_000


class DatabaseError(RuntimeError):
    """Base error for persistence failures shown safely in the UI."""


class DatabaseConfigurationError(DatabaseError):
    """Raised when Supabase secrets are missing or unsafe."""


class DatabaseUnavailableError(DatabaseError):
    """Raised when Supabase cannot be reached after retries."""


class ProfileAlreadyExistsError(DatabaseError):
    """Raised when a profile identifier is already registered."""


def normalize_name(value: str) -> str:
    """Create a stable, accent-insensitive identifier for profile lookup."""
    compact = " ".join(value.strip().split())
    decomposed = unicodedata.normalize("NFKD", compact)
    ascii_value = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return ascii_value.casefold()


def _read_secret(name: str) -> str | None:
    # Environment variables make the repository usable outside Streamlit Cloud.
    env_name = f"SUPABASE_{name.upper()}"
    env_value = os.getenv(env_name)
    if env_value:
        return env_value.strip()

    try:
        section = st.secrets.get("supabase", {})
        value = section.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return None


def get_supabase_settings() -> tuple[str, str]:
    url = _read_secret("url")
    key = (
        _read_secret("secret_key")
        or _read_secret("service_role_key")
        or _read_secret("key")
    )

    if not url or not key:
        raise DatabaseConfigurationError(
            "Faltan las credenciales de Supabase. Agrega url y secret_key en los Secrets de Streamlit."
        )
    if not url.startswith("https://") or ".supabase.co" not in url:
        raise DatabaseConfigurationError("La URL de Supabase no parece válida.")
    if key.startswith("sb_publishable_"):
        raise DatabaseConfigurationError(
            "Se configuró una publishable key. Esta app necesita una Secret key de servidor."
        )
    return url.rstrip("/"), key


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    url, key = get_supabase_settings()
    return create_client(
        url,
        key,
        options=ClientOptions(
            postgrest_client_timeout=12,
            storage_client_timeout=12,
            schema="public",
        ),
    )


def _error_code(exc: Exception) -> str:
    code = getattr(exc, "code", "")
    if code:
        return str(code)
    details = getattr(exc, "details", "")
    return f"{exc} {details}"


def _is_unique_violation(exc: Exception) -> bool:
    text = _error_code(exc).lower()
    return "23505" in text or "duplicate key" in text or "unique constraint" in text


def _is_missing_schema(exc: Exception) -> bool:
    text = _error_code(exc).lower()
    return (
        "42p01" in text
        or "does not exist" in text
        or "could not find the table" in text
        or "schema cache" in text
    )


def _run(operation: Callable[[], T], *, attempts: int = 3) -> T:
    """Retry transient API/network failures with short exponential backoff."""
    last_error: Exception | None = None
    for index in range(attempts):
        try:
            return operation()
        except Exception as exc:  # Supabase may wrap HTTP errors in different classes.
            last_error = exc
            if _is_unique_violation(exc) or _is_missing_schema(exc):
                raise
            if index < attempts - 1:
                time.sleep(0.35 * (2**index))

    raise DatabaseUnavailableError(
        "No pudimos comunicarnos con Supabase después de varios intentos. Tu progreso no fue descartado; vuelve a intentar."
    ) from last_error


def healthcheck() -> None:
    try:
        _run(lambda: get_client().table("profiles").select("id").limit(1).execute())
    except DatabaseConfigurationError:
        raise
    except Exception as exc:
        if _is_missing_schema(exc):
            raise DatabaseConfigurationError(
                "Supabase está conectado, pero faltan las tablas. Ejecuta supabase/schema.sql en el SQL Editor."
            ) from exc
        if isinstance(exc, DatabaseError):
            raise
        raise DatabaseUnavailableError(
            "Supabase respondió con un error. Revisa la URL, la Secret key y que el proyecto esté activo."
        ) from exc


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_profile(display_name: str, pin: str) -> dict[str, Any]:
    profile_id = str(uuid.uuid4())
    payload = {
        "id": profile_id,
        "display_name": display_name,
        "name_key": normalize_name(display_name),
        "pin_hash": hash_pin(pin),
    }
    try:
        response = _run(
            lambda: (
                get_client()
                .table("profiles")
                .upsert(payload, on_conflict="id")
                .execute()
            )
        )
    except Exception as exc:
        if _is_unique_violation(exc):
            raise ProfileAlreadyExistsError(
                "Ese nombre de usuario ya existe. Elige otro o entra con su clave."
            ) from exc
        if isinstance(exc, DatabaseError):
            raise
        raise DatabaseUnavailableError("No se pudo crear el perfil.") from exc

    data = response.data or []
    return data[0] if data else payload


def authenticate_profile(display_name: str, pin: str) -> dict[str, Any] | None:
    name_key = normalize_name(display_name)
    response = _run(
        lambda: (
            get_client()
            .table("profiles")
            .select("id,display_name,name_key,pin_hash,created_at")
            .eq("name_key", name_key)
            .limit(1)
            .execute()
        )
    )
    rows = response.data or []
    if not rows:
        # Run one hash anyway to reduce obvious timing differences.
        verify_pin(pin, hash_pin("000000"))
        return None
    profile = rows[0]
    if not verify_pin(pin, profile["pin_hash"]):
        return None
    profile.pop("pin_hash", None)
    return profile




def get_or_create_single_profile(display_name: str = "Perfil principal") -> dict[str, Any]:
    name_key = normalize_name(display_name)
    response = _run(
        lambda: (
            get_client()
            .table("profiles")
            .select("id,display_name,name_key,created_at")
            .eq("name_key", name_key)
            .limit(1)
            .execute()
        )
    )
    rows = response.data or []
    if rows:
        return rows[0]
    try:
        return create_profile(display_name, "000000")
    except ProfileAlreadyExistsError:
        response = _run(
            lambda: (
                get_client()
                .table("profiles")
                .select("id,display_name,name_key,created_at")
                .eq("name_key", name_key)
                .limit(1)
                .execute()
            )
        )
        rows = response.data or []
        if rows:
            return rows[0]
        raise DatabaseUnavailableError("No se pudo inicializar el perfil principal.")

def create_session(
    profile_id: str,
    mode: str,
    date_key: str,
    question_ids: list[str],
    created_at: str,
) -> str:
    session_id = str(uuid.uuid4())
    payload = {
        "id": session_id,
        "profile_id": profile_id,
        "mode": mode,
        "date_key": date_key,
        "question_ids": question_ids,
        "status": "active",
        "created_at": created_at,
    }

    try:
        # Upsert by deterministic ID makes a network retry safe if the first write succeeded.
        _run(
            lambda: (
                get_client()
                .table("quiz_sessions")
                .upsert(payload, on_conflict="id")
                .execute()
            )
        )
        return session_id
    except Exception as exc:
        # A concurrent tab can create the same daily challenge first.
        if mode == "daily" and _is_unique_violation(exc):
            existing = get_daily_session(profile_id, date_key)
            if existing:
                return str(existing["id"])
        if isinstance(exc, DatabaseError):
            raise
        raise DatabaseUnavailableError("No se pudo crear la sesión de preguntas.") from exc


def get_daily_session(profile_id: str, date_key: str) -> dict[str, Any] | None:
    response = _run(
        lambda: (
            get_client()
            .table("quiz_sessions")
            .select("*")
            .eq("profile_id", profile_id)
            .eq("date_key", date_key)
            .eq("mode", "daily")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    )
    rows = response.data or []
    return rows[0] if rows else None


def get_session(session_id: str) -> dict[str, Any] | None:
    response = _run(
        lambda: (
            get_client()
            .table("quiz_sessions")
            .select("*")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )
    )
    rows = response.data or []
    return rows[0] if rows else None


def _fetch_all(build_query: Callable[[], Any], *, page_size: int = 1000) -> list[dict[str, Any]]:
    """Fetch every row instead of silently stopping at Supabase's default limit."""
    rows: list[dict[str, Any]] = []
    start = 0
    while True:
        response = _run(
            lambda start=start: build_query().range(start, start + page_size - 1).execute()
        )
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
    return rows


def get_attempts_for_session(session_id: str) -> list[dict[str, Any]]:
    return _fetch_all(
        lambda: (
            get_client()
            .table("attempts")
            .select("*")
            .eq("session_id", session_id)
            .order("answered_at")
        )
    )


def get_user_attempts(profile_id: str) -> list[dict[str, Any]]:
    return _fetch_all(
        lambda: (
            get_client()
            .table("attempts")
            .select("*")
            .eq("profile_id", profile_id)
            .order("answered_at")
        )
    )


def get_user_sessions(profile_id: str) -> list[dict[str, Any]]:
    return _fetch_all(
        lambda: (
            get_client()
            .table("quiz_sessions")
            .select("*")
            .eq("profile_id", profile_id)
            .order("created_at")
        )
    )


def save_attempt(
    *,
    session_id: str,
    profile_id: str,
    question_id: str,
    topic: str,
    difficulty: str,
    selected_id: str,
    correct_id: str,
    response_ms: int,
    answered_at: str,
) -> bool:
    payload = {
        "session_id": session_id,
        "profile_id": profile_id,
        "question_id": question_id,
        "topic": topic,
        "difficulty": difficulty,
        "selected_id": selected_id,
        "correct_id": correct_id,
        "is_correct": selected_id == correct_id,
        "response_ms": max(0, response_ms),
        "answered_at": answered_at,
    }
    try:
        _run(lambda: get_client().table("attempts").insert(payload).execute())
        return True
    except Exception as exc:
        if _is_unique_violation(exc):
            # The answer was already persisted (double tap, rerun or ambiguous retry).
            return True
        if isinstance(exc, DatabaseError):
            raise
        raise DatabaseUnavailableError(
            "No se pudo confirmar la respuesta. No avances hasta volver a intentarlo."
        ) from exc


def mark_completed(session_id: str, completed_at: str) -> None:
    _run(
        lambda: (
            get_client()
            .table("quiz_sessions")
            .update({"status": "completed", "completed_at": completed_at})
            .eq("id", session_id)
            .eq("status", "active")
            .execute()
        )
    )
