from rest_framework import serializers
from django.utils import timezone
from django.db.models import Sum

from .models import (
    Colaborador,
    Insumo,
    Pedido,
    Produto,
    ProdutoPronto,
    ProdutoVenda
)


# =========================================================
# PRODUTO
# =========================================================

class ProdutoSerializer(serializers.ModelSerializer):
    preco = serializers.SerializerMethodField()
    quantidade_pronta = serializers.SerializerMethodField()
    data_fabricacao_pronta = serializers.SerializerMethodField()
    data_validade_pronta = serializers.SerializerMethodField()
    peso_produto_pronto = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            'id', 'codigo', 'nome', 'categoria', 'data_fabricacao',
            'data_validade', 'quantidade', 'catalogo', 'preco',
            'quantidade_pronta', 'data_fabricacao_pronta',
            'data_validade_pronta', 'peso_produto_pronto'
        ]

    # ========================
    # LOTES VÁLIDOS (BASE DO SISTEMA)
    # ========================
    def get_lotes_catalogo(self, obj):
        """
        Retorna apenas lotes NÃO vencidos e com quantidade > 0
        """
        if obj.catalogo:
            return ProdutoPronto.objects.filter(
                catalogo=obj.catalogo,
                data_validade__gte=timezone.now().date(),
                quantidade__gt=0
            )
        return ProdutoPronto.objects.none()

    # ========================
    # PREÇO DO PRODUTO
    # ========================
    def get_preco(self, obj):
        produto_pronto = self.get_lotes_catalogo(
            obj).order_by('data_validade').first()

        if not produto_pronto:
            return None

        venda = ProdutoVenda.objects.filter(
            produto_pronto=produto_pronto,
            ativo=True
        ).first()

        return venda.preco if venda else None

    # ========================
    # DADOS DO PRODUTO PRONTO
    # ========================
    def get_quantidade_pronta(self, obj):
        lotes = self.get_lotes_catalogo(obj)
        return sum(l.quantidade for l in lotes)

    def get_data_fabricacao_pronta(self, obj):
        lotes = self.get_lotes_catalogo(obj)
        datas = [l.data_fabricacao for l in lotes if l.data_fabricacao]
        return min(datas) if datas else None

    def get_data_validade_pronta(self, obj):
        lotes = self.get_lotes_catalogo(obj)
        datas = [l.data_validade for l in lotes if l.data_validade]
        return min(datas) if datas else None  # mais próximo do vencimento

    def get_peso_produto_pronto(self, obj):
        lotes = self.get_lotes_catalogo(obj)
        pesos = [l.peso_produto for l in lotes if l.peso_produto]
        return sum(pesos) if pesos else None

    # ========================
    # CREATE
    # ========================
    def create(self, validated_data):
        produtovenda_data = validated_data.pop('produtovenda', None)

        produto = Produto.objects.create(**validated_data)

        if produtovenda_data:
            preco = produtovenda_data.get('preco')

            produto_pronto = ProdutoPronto.objects.filter(
                catalogo=produto.catalogo,
                data_validade__gte=timezone.now().date()
            ).order_by('data_validade').first()

            if produto_pronto and preco:
                ProdutoVenda.objects.create(
                    produto_pronto=produto_pronto,
                    codigo_externo=f"PV-{produto.id}-{produto_pronto.id}",
                    preco=preco,
                    ativo=True
                )

        return produto

    # ========================
    # UPDATE
    # ========================
    def update(self, instance, validated_data):
        preco_data = validated_data.pop('produtovenda', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if preco_data:
            produto_pronto = ProdutoPronto.objects.filter(
                catalogo=instance.catalogo,
                data_validade__gte=timezone.now().date()
            ).order_by('data_validade').first()

            if produto_pronto:
                ProdutoVenda.objects.update_or_create(
                    produto_pronto=produto_pronto,
                    defaults={
                        'preco': preco_data.get('preco', 0),
                        'ativo': True
                    }
                )

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['data_validade'] = data.get('data_validade_pronta')
        return data
# =========================================================
# INSUMO
# =========================================================


class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        fields = '__all__'


# =========================================================
# COLABORADOR
# =========================================================

class ColaboradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colaborador
        fields = '__all__'


# =========================================================
# PRODUTO VENDA
# =========================================================

class ProdutoVendaSerializer(serializers.ModelSerializer):

    nome_produto = serializers.SerializerMethodField()
    estoque_total = serializers.SerializerMethodField()

    class Meta:
        model = ProdutoVenda
        fields = [
            'id',
            'codigo_externo',
            'nome_produto',
            'preco',
            'estoque_total',
            'ativo'
        ]

    def get_nome_produto(self, obj):
        return obj.produto_pronto.catalogo.nome

    def get_estoque_total(self, obj):
        total = ProdutoPronto.objects.filter(
            catalogo=obj.produto_pronto.catalogo
        ).aggregate(total=Sum('quantidade'))['total'] or 0

        return int(total)

# =========================================================
# PEDIDO
# =========================================================


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = "__all__"
