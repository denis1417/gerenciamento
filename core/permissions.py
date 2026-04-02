from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Permite leitura para usuários autenticados,
    mas escrita apenas para superusuários.
    """

    def has_permission(self, request, view):

        # Permitir GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # Permitir apenas superusuário
        return request.user.is_superuser
