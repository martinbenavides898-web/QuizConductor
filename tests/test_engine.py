from collections import Counter
from datetime import timedelta

from app.data import load_questions
from app.engine import (
    calculate_streak,
    displayed_options,
    now_local,
    ordered_options,
    select_questions,
    stable_seed,
)


def test_daily_selection_has_exact_mix_and_no_duplicates():
    questions = load_questions()
    selected_ids = select_questions(
        questions,
        attempts=[],
        seed=stable_seed("profile", "2026-08-02", "daily"),
        mix={"easy": 3, "medium": 4, "hard": 3},
    )
    by_id = {question["id"]: question for question in questions}
    assert len(selected_ids) == 10
    assert len(set(selected_ids)) == 10
    assert Counter(by_id[qid]["difficulty"] for qid in selected_ids) == {
        "easy": 3,
        "medium": 4,
        "hard": 3,
    }


def test_option_order_is_stable_per_session_and_keeps_all_options():
    question = load_questions()[0]
    first = ordered_options(question, "session-1")
    second = ordered_options(question, "session-1")
    assert [option["id"] for option in first] == [option["id"] for option in second]
    assert {option["id"] for option in first} == {"A", "B", "C", "D"}


def test_streak_counts_completed_daily_sessions_only():
    today = now_local().date()
    sessions = [
        {"mode": "daily", "status": "completed", "date_key": today.isoformat()},
        {
            "mode": "daily",
            "status": "completed",
            "date_key": (today - timedelta(days=1)).isoformat(),
        },
        {
            "mode": "practice",
            "status": "completed",
            "date_key": (today - timedelta(days=2)).isoformat(),
        },
    ]
    assert calculate_streak(sessions) == 2


def test_displayed_options_are_labeled_in_visible_order():
    question = load_questions()[0]
    rows = displayed_options(question, "session-1")
    assert [row["display_id"] for row in rows] == ["A", "B", "C", "D"]
    assert {row["option_id"] for row in rows} == {"A", "B", "C", "D"}
    assert rows == displayed_options(question, "session-1")
