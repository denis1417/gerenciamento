from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import ProdutoPronto


@transaction.atomic
def baixar_estoque_fifo(produto_venda, quantidade):

    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    lotes = ProdutoPronto.objects.select_for_update().filter(
        catalogo=produto_venda.produto_pronto.catalogo,
        data_validade__gte=timezone.now().date(),
        quantidade__gt=0
    ).order_by("data_validade")

    estoque_total = lotes.aggregate(total=Sum("quantidade"))["total"] or 0

    if quantidade > estoque_total:
        raise ValueError(f"Estoque insuficiente. Disponível: {estoque_total}")

    restante = quantidade

    for lote in lotes:

        if restante <= 0:
            break

        if lote.quantidade >= restante:
            lote.quantidade -= restante
            lote.save()
            restante = 0

        else:
            restante -= lote.quantidade
            lote.quantidade = 0
            lote.save()
