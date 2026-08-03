from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "data" / "questions.json"
OFFICIAL_BOOK_PATH = ROOT / "docs" / "Libro_oficial_CONASET_Clase_B_2024.pdf"
ICON_PATH = ROOT / "assets" / "cplus_icon.png"

APP_NAME = "Conduce+"
APP_VERSION = "0.3.0"
TIMEZONE = "America/Santiago"
DAILY_MIX = {"easy": 3, "medium": 4, "hard": 3}
