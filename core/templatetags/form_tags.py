from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css):
    """
    Adiciona classe CSS ao campo preservando atributos existentes como type='date'
    """
    # Pega os atributos existentes do widget
    existing_attrs = field.field.widget.attrs.copy()
    # Adiciona ou sobrescreve a classe
    existing_attrs['class'] = css
    # Renderiza o widget com todos os atributos preservados
    return field.as_widget(attrs=existing_attrs)
