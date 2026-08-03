from __future__ import annotations

import calendar as calendar_lib
from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.config import TIMEZONE


def parse_local_day(value: object) -> date | None:
    """Convert a Supabase timestamp to the Chilean calendar day."""
    if value is None:
        return None
    try:
        timestamp = pd.to_datetime(value, utc=True)
        return timestamp.tz_convert(TIMEZONE).date()
    except (ValueError, TypeError, AttributeError):
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def normalize_date_key(value: object) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def build_accuracy_trend(
    attempts: list[dict[str, Any]],
    *,
    today: date | None = None,
    window_days: int = 30,
) -> pd.DataFrame:
    """Return a complete date range with daily and cumulative accuracy."""
    if window_days < 1:
        raise ValueError("window_days debe ser mayor que cero")

    records: list[dict[str, Any]] = []
    for attempt in attempts:
        day = parse_local_day(attempt.get("answered_at"))
        if day:
            records.append({"Fecha": day, "Correcta": int(attempt["is_correct"])})

    if not records:
        return pd.DataFrame(
            columns=["Fecha", "Precisión diaria", "Precisión acumulada", "Respuestas"]
        )

    raw = pd.DataFrame(records)
    daily = (
        raw.groupby("Fecha", as_index=False)
        .agg(Correctas=("Correcta", "sum"), Respuestas=("Correcta", "size"))
        .sort_values("Fecha")
    )
    daily["Precisión diaria"] = daily["Correctas"] / daily["Respuestas"] * 100
    daily["Correctas acumuladas"] = daily["Correctas"].cumsum()
    daily["Respuestas acumuladas"] = daily["Respuestas"].cumsum()
    daily["Precisión acumulada"] = (
        daily["Correctas acumuladas"] / daily["Respuestas acumuladas"] * 100
    )

    current_day = today or date.today()
    first_visible = max(daily["Fecha"].min(), current_day - timedelta(days=window_days - 1))
    full_range = pd.DataFrame(
        {"Fecha": pd.date_range(first_visible, current_day, freq="D").date}
    )
    trend = full_range.merge(
        daily[["Fecha", "Precisión diaria", "Precisión acumulada", "Respuestas"]],
        on="Fecha",
        how="left",
    )

    previous = daily[daily["Fecha"] < first_visible]
    if not previous.empty and pd.isna(trend.loc[0, "Precisión acumulada"]):
        trend.loc[0, "Precisión acumulada"] = float(
            previous.iloc[-1]["Precisión acumulada"]
        )
    trend["Precisión acumulada"] = trend["Precisión acumulada"].ffill()
    trend["Fecha"] = pd.to_datetime(trend["Fecha"])
    return trend


def move_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_weeks(year: int, month: int) -> list[list[int]]:
    """Return a Monday-first month matrix padded with zeros."""
    calendar = calendar_lib.Calendar(firstweekday=calendar_lib.MONDAY)
    return calendar.monthdayscalendar(year, month)


def activity_day_sets(
    sessions: list[dict[str, Any]], attempts: list[dict[str, Any]]
) -> tuple[set[date], set[date], set[date]]:
    completed_days: set[date] = set()
    started_daily_days: set[date] = set()
    for session in sessions:
        if session.get("mode") != "daily":
            continue
        day = normalize_date_key(session.get("date_key"))
        if not day:
            continue
        if session.get("status") == "completed":
            completed_days.add(day)
        else:
            started_daily_days.add(day)

    activity_days = {
        day
        for attempt in attempts
        if (day := parse_local_day(attempt.get("answered_at"))) is not None
    }
    return completed_days, started_daily_days, activity_days
