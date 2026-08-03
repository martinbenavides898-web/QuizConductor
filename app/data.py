from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import QUESTIONS_PATH


@lru_cache(maxsize=1)
def load_questions() -> list[dict[str, Any]]:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as fh:
        questions = json.load(fh)
    validate_questions(questions)
    return questions


def validate_questions(questions: list[dict[str, Any]]) -> None:
    if not questions:
        raise ValueError("El banco de preguntas está vacío.")

    required = {
        "id", "type", "topic", "subtopic", "difficulty", "prompt",
        "options", "correct_id", "explanation", "tip", "source", "status"
    }
    ids: set[str] = set()
    for question in questions:
        missing = required - set(question)
        if missing:
            raise ValueError(f"Pregunta {question.get('id', '?')} incompleta: {missing}")
        if question["id"] in ids:
            raise ValueError(f"ID duplicado: {question['id']}")
        ids.add(question["id"])
        if question["difficulty"] not in {"easy", "medium", "hard"}:
            raise ValueError(f"Dificultad inválida: {question['id']}")
        option_ids = {option["id"] for option in question["options"]}
        if len(option_ids) != 4 or question["correct_id"] not in option_ids:
            raise ValueError(f"Alternativas inválidas: {question['id']}")
        source = question["source"]
        if not source.get("document") or not source.get("page"):
            raise ValueError(f"Fuente incompleta: {question['id']}")


def question_map() -> dict[str, dict[str, Any]]:
    return {q["id"]: q for q in load_questions()}
