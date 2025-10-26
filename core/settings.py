from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv  # type: ignore[reportMissingImports]
    load_dotenv()
except Exception:
    pass

FIRESTORE_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "projeto-integrador-2-31637")
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")

GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(BASE_DIR / "secrets" / "django-firestore-key.json")
)
