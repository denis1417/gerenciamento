# from django.http import JsonResponse
# from core.services.firestore_client import get_db
# from google.auth import default as google_auth_default

# def firestore_ping(request):
#     try:
#         creds, proj = google_auth_default()
#         print("ADC:", type(creds).__name__, getattr(creds, "service_account_email", None), "proj:", proj)
#     except Exception as e:
#         print("Sem ADC:", e)
#     db = get_db()
#     doc_ref = db.collection("healthcheck").document("ping")
#     doc_ref.set({"ok": True})
#     snap = doc_ref.get()
#     return JsonResponse({"exists": snap.exists, "data": snap.to_dict()})
# TEMPORÁRIO: substitua o corpo do firestore_ping por este bloco
from django.http import JsonResponse
from google.oauth2 import service_account
from google.cloud import firestore
from django.conf import settings

import os

def firestore_ping(request):
    print("KEY PATH (settings):", settings.GOOGLE_APPLICATION_CREDENTIALS,
          "exists:", os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS))
    print("KEY PATH:", settings.GOOGLE_APPLICATION_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS)
    print("SA EMAIL:", creds.service_account_email, "PROJECT(from key):", creds.project_id)
    db = firestore.Client(project=creds.project_id, credentials=creds)
    doc_ref = db.collection("healthcheck").document("ping")
    doc_ref.set({"ok": True})
    snap = doc_ref.get()
    return JsonResponse({"exists": snap.exists, "data": snap.to_dict()})