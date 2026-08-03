from collections import Counter

from app.data import load_questions


def test_question_bank_is_valid():
    questions = load_questions()
    assert len(questions) >= 40
    assert len({q["id"] for q in questions}) == len(questions)
    assert Counter(q["difficulty"] for q in questions) == {
        "easy": 14,
        "medium": 14,
        "hard": 14,
    }
    for question in questions:
        assert len(question["options"]) == 4
        assert question["correct_id"] in {o["id"] for o in question["options"]}
        assert question["source"]["page"] > 0
        assert question["status"] == "verified_from_official_source"
