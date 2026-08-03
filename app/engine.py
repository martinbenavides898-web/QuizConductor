from __future__ import annotations

import hashlib
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.config import DAILY_MIX, TIMEZONE


def now_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


def local_date_key() -> str:
    return now_local().date().isoformat()


def stable_seed(*parts: str) -> int:
    raw = "|".join(parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def _history_profile(attempts: list[dict[str, Any]]) -> tuple[dict[str, float], Counter]:
    totals: dict[str, int] = defaultdict(int)
    correct: dict[str, int] = defaultdict(int)
    seen: Counter = Counter()
    for attempt in attempts:
        totals[attempt["topic"]] += 1
        correct[attempt["topic"]] += int(attempt["is_correct"])
        seen[attempt["question_id"]] += 1

    weakness: dict[str, float] = {}
    for topic, total in totals.items():
        # Bayesian smoothing: avoids overreacting to one answer.
        accuracy = (correct[topic] + 1.5) / (total + 3)
        weakness[topic] = 1.0 - accuracy
    return weakness, seen


def select_questions(
    questions: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    *,
    seed: int,
    mix: dict[str, int] | None = None,
) -> list[str]:
    rng = random.Random(seed)
    mix = mix or DAILY_MIX
    weakness, seen = _history_profile(attempts)
    selected: list[dict[str, Any]] = []
    topic_counter: Counter = Counter()

    for difficulty, quantity in mix.items():
        pool = [q for q in questions if q["difficulty"] == difficulty]
        for _ in range(quantity):
            if not pool:
                break
            weights: list[float] = []
            for q in pool:
                topic_need = weakness.get(q["topic"], 0.52)
                novelty = 1.0 / (1.0 + seen[q["id"]])
                diversity = 1.0 / (1.0 + 0.75 * topic_counter[q["topic"]])
                weight = (1.0 + 2.8 * topic_need + 1.2 * novelty) * diversity
                weights.append(max(0.05, weight))
            chosen = rng.choices(pool, weights=weights, k=1)[0]
            selected.append(chosen)
            topic_counter[chosen["topic"]] += 1
            pool.remove(chosen)

    rng.shuffle(selected)
    return [q["id"] for q in selected]


def ordered_options(question: dict[str, Any], session_id: str) -> list[dict[str, Any]]:
    options = list(question["options"])
    random.Random(stable_seed(session_id, question["id"], "options")).shuffle(options)
    return options


def build_session_summary(
    attempts: list[dict[str, Any]],
    questions_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    total = len(attempts)
    correct = sum(int(a["is_correct"]) for a in attempts)
    accuracy = (correct / total * 100) if total else 0.0
    avg_seconds = (sum(a["response_ms"] for a in attempts) / total / 1000) if total else 0.0

    topic_data: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    for attempt in attempts:
        topic = questions_by_id[attempt["question_id"]]["topic"]
        topic_data[topic]["total"] += 1
        topic_data[topic]["correct"] += int(attempt["is_correct"])

    ranked = sorted(
        (
            {
                "topic": topic,
                "accuracy": data["correct"] / data["total"] * 100,
                **data,
            }
            for topic, data in topic_data.items()
        ),
        key=lambda item: item["accuracy"],
    )
    weakest = ranked[0] if ranked else None
    strongest = ranked[-1] if ranked else None

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_seconds": avg_seconds,
        "weakest": weakest,
        "strongest": strongest,
        "topics": ranked,
    }


def calculate_streak(sessions: list[dict[str, Any]]) -> int:
    completed_days = {
        session["date_key"]
        for session in sessions
        if session["mode"] == "daily" and session["status"] == "completed"
    }
    today = now_local().date()
    # Allow the streak to remain visible before today's challenge is completed.
    cursor = today if today.isoformat() in completed_days else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in completed_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def xp_from_data(attempts: list[dict[str, Any]], sessions: list[dict[str, Any]]) -> int:
    correct = sum(int(a["is_correct"]) for a in attempts)
    incorrect = len(attempts) - correct
    completed = sum(1 for s in sessions if s["status"] == "completed")
    return correct * 12 + incorrect * 4 + completed * 20
