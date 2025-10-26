from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .repos_colaboradores import ColaboradoresRepo

repo = ColaboradoresRepo()

@require_http_methods(["GET"])
def fs_colaboradores_list(request):
    try:
        limit = int(request.GET.get("limit", 50))
        start_after = request.GET.get("start_after")
        items = repo.list(limit=limit, start_after_id=start_after)
        return JsonResponse(items, safe=False)
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
@require_http_methods(["POST"])
def fs_colaboradores_create(request):
    try:
        data = json.loads(request.body or "{}")
        created = repo.create_colab(data)
        return JsonResponse(created, status=201)
    except ValueError as ve:
        return HttpResponseBadRequest(str(ve))
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def fs_colaboradores_detail(request, doc_id: str):
    if request.method == "GET":
        obj = repo.get(doc_id)
        return JsonResponse(obj) if obj else HttpResponseNotFound("Não encontrado")

    if request.method == "PUT":
        try:
            data = json.loads(request.body or "{}")
            obj = repo.update_colab(doc_id, data)
            return JsonResponse(obj)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

    if request.method == "DELETE":
        repo.delete(doc_id)
        return JsonResponse({"ok": True}, status=204)
