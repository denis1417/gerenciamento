from rest_framework import serializers
from .models import Produto, Insumo, Colaborador, Pedido
from .models import Produto, ProdutoPronto, ProdutoVenda


class ProdutoSerializer(serializers.ModelSerializer):

    preco = serializers.SerializerMethodField()

    # Campos do ProdutoPronto relacionados ao mesmo catálogo
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
    # PREÇO DO PRODUTO
    # ========================
    def get_preco(self, obj):

        produto_pronto = ProdutoPronto.objects.filter(
            catalogo=obj.catalogo
        ).first()

        if not produto_pronto:
            return None

        venda = ProdutoVenda.objects.filter(
            produto_pronto=produto_pronto,
            ativo=True
        ).first()

        if venda:
            return venda.preco

        return None

    # ========================
    # MÉTODOS PARA PRODUTOPRONTO
    # ========================
    def get_produto_pronto(self, obj):
        """Retorna o primeiro ProdutoPronto do mesmo catálogo"""
        if obj.catalogo:
            return obj.catalogo.produtos.first()
        return None

    def get_quantidade_pronta(self, obj):
        produto_pronto = self.get_produto_pronto(obj)
        return produto_pronto.quantidade if produto_pronto else None

    def get_data_fabricacao_pronta(self, obj):
        produto_pronto = self.get_produto_pronto(obj)
        return produto_pronto.data_fabricacao if produto_pronto else None

    def get_data_validade_pronta(self, obj):
        produto_pronto = self.get_produto_pronto(obj)
        return produto_pronto.data_validade if produto_pronto else None

    def get_peso_produto_pronto(self, obj):
        produto_pronto = self.get_produto_pronto(obj)
        return produto_pronto.peso_produto if produto_pronto else None

    # ========================
    # CRIAR / ATUALIZAR PRODUTOVENDA
    # ========================
    def create(self, validated_data):
        produtovenda_data = validated_data.pop('produtovenda', None)

        produto = Produto.objects.create(**validated_data)

        if produtovenda_data:
            preco = produtovenda_data.get('preco')

            produto_pronto = ProdutoPronto.objects.filter(
                catalogo=produto.catalogo
            ).first()

            if produto_pronto and preco:
                ProdutoVenda.objects.create(
                    produto_pronto=produto_pronto,
                    codigo_externo=f"PV-{produto.id}-{produto_pronto.id}",
                    preco=preco,
                    ativo=True
                )

        return produto

    def update(self, instance, validated_data):
        preco_data = validated_data.pop('produtovenda', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if preco_data:
            ProdutoVenda.objects.update_or_create(
                produto_pronto=self.get_produto_pronto(instance),
                defaults={'preco': preco_data.get('preco', 0), 'ativo': True}
            )

        return instance


class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        fields = '__all__'


class ColaboradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colaborador
        fields = '__all__'


class ProdutoVendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdutoVenda
        fields = ["codigo_externo", "preco", "ativo"]


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = "__all__"
