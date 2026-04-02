# core/context_processors.py
def group_permissions(request):
    if request.user.is_authenticated:
        return {
            "is_admin": request.user.is_superuser,
            "is_rh": request.user.groups.filter(name="RH").exists() or request.user.is_superuser,
            "is_insumo": request.user.groups.filter(name="Insumos").exists() or request.user.is_superuser,
            "is_confeitaria": request.user.groups.filter(name="Confeitaria").exists() or request.user.is_superuser,
        }
    return {}
