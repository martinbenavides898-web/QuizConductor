from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import QUESTIONS_PATH


ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
ALLOWED_TYPES = {"conceptual", "situacion_real", "situacion_compleja", "calculo_aplicado"}
EXPECTED_OPTION_IDS = {"A", "B", "C", "D"}


@lru_cache(maxsize=1)
def load_questions() -> list[dict[str, Any]]:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as file_handle:
        questions = json.load(file_handle)
    validate_questions(questions)
    return questions


def _require_text(value: object, *, label: str, question_id: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} vacío o inválido en {question_id}.")


def validate_questions(questions: list[dict[str, Any]]) -> None:
    if not questions:
        raise ValueError("El banco de preguntas está vacío.")

    required = {
        "id",
        "type",
        "topic",
        "subtopic",
        "difficulty",
        "prompt",
        "options",
        "correct_id",
        "explanation",
        "tip",
        "source",
        "status",
    }
    ids: set[str] = set()

    for question in questions:
        question_id = str(question.get("id", "?"))
        missing = required - set(question)
        if missing:
            raise ValueError(f"Pregunta {question_id} incompleta: {sorted(missing)}")
        if question_id in ids:
            raise ValueError(f"ID duplicado: {question_id}")
        ids.add(question_id)

        for field in ("id", "topic", "subtopic", "prompt", "explanation", "tip"):
            _require_text(question[field], label=field, question_id=question_id)

        if question["difficulty"] not in ALLOWED_DIFFICULTIES:
            raise ValueError(f"Dificultad inválida: {question_id}")
        if question["type"] not in ALLOWED_TYPES:
            raise ValueError(f"Tipo de pregunta inválido: {question_id}")
        if question["status"] != "verified_from_official_source":
            raise ValueError(f"Pregunta no verificada: {question_id}")

        options = question["options"]
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Deben existir cuatro alternativas: {question_id}")
        option_ids = {option.get("id") for option in options}
        if option_ids != EXPECTED_OPTION_IDS:
            raise ValueError(f"IDs de alternativas inválidos: {question_id}")
        if question["correct_id"] not in option_ids:
            raise ValueError(f"Respuesta correcta inválida: {question_id}")
        for option in options:
            _require_text(option.get("text"), label="texto de alternativa", question_id=question_id)
            _require_text(option.get("feedback"), label="retroalimentación", question_id=question_id)

        source = question["source"]
        for field in ("document", "chapter", "section"):
            _require_text(source.get(field), label=f"fuente.{field}", question_id=question_id)
        page = source.get("page")
        if not isinstance(page, int) or not 1 <= page <= 170:
            raise ValueError(f"Página de fuente inválida: {question_id}")


def question_map() -> dict[str, dict[str, Any]]:
    return {question["id"]: question for question in load_questions()}
