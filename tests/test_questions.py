from collections import Counter

from app.data import load_questions


def test_question_bank_is_valid_and_balanced():
    questions = load_questions()
    assert len(questions) == 42
    assert len({question["id"] for question in questions}) == len(questions)
    assert Counter(question["difficulty"] for question in questions) == {
        "easy": 14,
        "medium": 14,
        "hard": 14,
    }
    for question in questions:
        assert [option["id"] for option in question["options"]] == ["A", "B", "C", "D"]
        assert question["correct_id"] in {option["id"] for option in question["options"]}
        assert all(option["text"].strip() for option in question["options"])
        assert all(option["feedback"].strip() for option in question["options"])
        assert 1 <= question["source"]["page"] <= 170
        assert question["status"] == "verified_from_official_source"


def test_corrected_advertising_sources_point_to_exact_pages():
    by_id = {question["id"]: question for question in load_questions()}
    assert by_id["Q039"]["source"]["page"] == 101
    assert by_id["Q040"]["source"]["page"] == 102
