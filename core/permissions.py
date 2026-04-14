from rest_framework.permissions import SAFE_METHODS, BasePermission


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


class IsAdminSistema(BasePermission):
    """
    Permite acesso apenas para colaboradores marcados como admin
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if hasattr(user, 'colaborador'):
            return user.colaborador.is_admin

        return False
