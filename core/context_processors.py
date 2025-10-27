# core/context_processors.py
from django.conf import settings

def group_permissions(request):
    context = {
        "MEDIA_URL": settings.MEDIA_URL,  # Adiciona MEDIA_URL aos templates
    }
    
    if request.user.is_authenticated:
        context.update({
            "is_admin": request.user.is_superuser,
            "is_rh": request.user.groups.filter(name="RH").exists() or request.user.is_superuser,
            "is_insumo": request.user.groups.filter(name="Insumos").exists() or request.user.is_superuser,
            "is_confeitaria": request.user.groups.filter(name="Confeitaria").exists() or request.user.is_superuser,
        })
    
    return context
