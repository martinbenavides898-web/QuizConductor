import pytest

pytest.importorskip("streamlit")
pytest.importorskip("supabase")

from app.database import hash_pin, normalize_name, verify_pin


def test_name_normalization_is_stable():
    assert normalize_name("  Válentina   Pérez ") == "valentina perez"


def test_pin_is_hashed_and_verifiable():
    encoded = hash_pin("123456")
    assert "123456" not in encoded
    assert verify_pin("123456", encoded)
    assert not verify_pin("654321", encoded)
