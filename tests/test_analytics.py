from datetime import date

from app.analytics import (
    activity_day_sets,
    build_accuracy_trend,
    month_weeks,
    move_month,
    parse_local_day,
)


def test_supabase_timestamp_uses_chilean_day():
    assert parse_local_day("2026-08-03T02:30:00+00:00") == date(2026, 8, 2)


def test_accuracy_trend_fills_dates_and_keeps_daily_and_cumulative_values():
    attempts = [
        {"answered_at": "2026-08-01T12:00:00-04:00", "is_correct": True},
        {"answered_at": "2026-08-01T12:01:00-04:00", "is_correct": False},
        {"answered_at": "2026-08-03T12:00:00-04:00", "is_correct": True},
    ]
    trend = build_accuracy_trend(attempts, today=date(2026, 8, 3), window_days=30)
    assert list(trend["Fecha"].dt.date) == [
        date(2026, 8, 1),
        date(2026, 8, 2),
        date(2026, 8, 3),
    ]
    assert trend.loc[0, "Precisión diaria"] == 50
    assert trend.loc[2, "Precisión diaria"] == 100
    assert round(trend.loc[2, "Precisión acumulada"], 2) == 66.67


def test_month_grid_is_monday_first_and_calendar_navigation_wraps_year():
    weeks = month_weeks(2026, 8)
    assert weeks[0] == [0, 0, 0, 0, 0, 1, 2]
    assert move_month(2026, 1, -1) == (2025, 12)
    assert move_month(2026, 12, 1) == (2027, 1)


def test_activity_sets_distinguish_completed_started_and_practice():
    sessions = [
        {"mode": "daily", "status": "completed", "date_key": "2026-08-01"},
        {"mode": "daily", "status": "active", "date_key": "2026-08-02"},
    ]
    attempts = [
        {"answered_at": "2026-08-03T12:00:00-04:00", "is_correct": True}
    ]
    completed, started, activity = activity_day_sets(sessions, attempts)
    assert completed == {date(2026, 8, 1)}
    assert started == {date(2026, 8, 2)}
    assert activity == {date(2026, 8, 3)}
