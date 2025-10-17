from django import template

register = template.Library()


@register.filter
def formatar_quantidade(valor, unidade):
    """
    Formata uma quantidade, tratando litros/ml e gramas/ml automaticamente.
    """
    if unidade.lower() == 'ml':
        # valor vem em ml
        litros = int(valor // 1000)
        ml = int(valor % 1000)
        if litros:
            return f"{litros} L e {ml} ml"
        return f"{ml} ml"

    if unidade.lower() == 'g':
        # valor vem em g
        kg = int(valor // 1000)
        g = int(valor % 1000)
        if kg:
            return f"{kg} kg e {g} g"
        return f"{g} g"

    # outros tipos de unidade
    return f"{valor} {unidade}"


@register.filter
def multiplicar(valor, fator):
    """Multiplica valor por fator (útil para conversão L→ml, kg→g, etc)."""
    return float(valor) * float(fator)
