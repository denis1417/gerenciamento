from functools import lru_cache
from google.cloud import firestore
from google.oauth2 import service_account
from django.conf import settings
import os

@lru_cache(maxsize=1)
def get_db() -> firestore.Client:
    if getattr(settings, "FIRESTORE_EMULATOR_HOST", None):
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST

    key_path = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)
    if key_path and os.path.exists(key_path):
        creds = service_account.Credentials.from_service_account_file(key_path)
        project = getattr(settings, "FIRESTORE_PROJECT_ID", None) or creds.project_id
        return firestore.Client(project=project, credentials=creds)

    project = getattr(settings, "FIRESTORE_PROJECT_ID", None) or None
    return firestore.Client(project=project)
