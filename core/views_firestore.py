from django.http import JsonResponse
from core.services.firestore_client import get_db

def firestore_ping(request):
    db = get_db()
    doc_ref = db.collection("healthcheck").document("ping")
    doc_ref.set({"ok": True})
    snap = doc_ref.get()
    return JsonResponse({"exists": snap.exists, "data": snap.to_dict()})
