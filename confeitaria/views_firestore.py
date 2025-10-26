from django.http import JsonResponse
from google.oauth2 import service_account
from google.cloud import firestore
from django.conf import settings
import os

def firestore_ping(request):
    creds = service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS)
    db = firestore.Client(project=creds.project_id, credentials=creds)
    doc_ref = db.collection("healthcheck").document("ping")
    doc_ref.set({"ok": True})
    snap = doc_ref.get()
    return JsonResponse({"exists": snap.exists, "data": snap.to_dict()})