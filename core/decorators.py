from django.contrib.auth.decorators import user_passes_test


def check_group(groups):
    """
    Decorator que verifica se o usuário pertence a um ou mais grupos específicos.
    Aceita string (um grupo) ou lista/tupla (vários grupos).
    Superusuários têm acesso automático.
    """
    def in_group(user):
        if not user.is_authenticated:
            return False

        # Se for string, transforma em lista
        if isinstance(groups, str):
            groups_list = [groups]
        else:
            groups_list = groups

        # Verifica se o usuário pertence a algum dos grupos
        return user.is_superuser or user.groups.filter(name__in=groups_list).exists()

    return user_passes_test(in_group)
