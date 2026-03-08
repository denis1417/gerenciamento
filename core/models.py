from django.db import models
from django.contrib.auth.models import User
import uuid


def gerar_codigo():
    return str(uuid.uuid4())[:8]

# ------------------ CATALOGO PRODUTO ------------------


class CatalogoProduto(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# ------------------ PRODUTO ------------------

class Produto(models.Model):
    catalogo = models.ForeignKey(
        CatalogoProduto,
        on_delete=models.PROTECT,
        related_name="lotes",
        null=True,
        blank=True
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
        default=gerar_codigo
    )
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    data_fabricacao = models.DateField()
    data_validade = models.DateField(null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


# ------------------ PRODUTO PRONTO ------------------

class ProdutoPronto(models.Model):
    catalogo = models.ForeignKey(
        CatalogoProduto,
        on_delete=models.PROTECT,
        related_name="produtos",
        null=True,
        blank=True,
    )
    quantidade = models.FloatField(default=0)
    data_fabricacao = models.DateField()
    data_validade = models.DateField()
    peso_produto = models.FloatField(default=0)

    def __str__(self):
        return f"{self.catalogo.nome if self.catalogo else 'Sem catálogo'} - {self.quantidade} unidades"


# ------------------ COLABORADOR ------------------

class Colaborador(models.Model):
    rc = models.CharField(max_length=20, unique=True,
                          verbose_name="Registro de Colaborador")
    nome = models.CharField(max_length=100)
    data_nascimento = models.DateField()
    sexo = models.CharField(max_length=10, choices=[
                            ("M", "Masculino"), ("F", "Feminino")])
    funcao = models.CharField(max_length=50)
    CPF_RG = models.CharField(max_length=20, unique=True)
    foto = models.ImageField(upload_to="colaboradores/", blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    logradouro = models.CharField(max_length=100, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=50, blank=True, null=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    complemento = models.CharField(max_length=50, blank=True, null=True)
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='colaborador')

    def __str__(self):
        return self.nome


# ------------------ INSUMO ------------------

class Insumo(models.Model):
    UNIDADES = [
        ("g", "Grama"),
        ("ml", "Mililitro"),
        ("un", "Unidade"),
    ]

    nome = models.CharField(max_length=100)
    quantidade_total = models.FloatField(default=0)
    unidade_base = models.CharField(
        max_length=10, choices=UNIDADES, default="un")

    def __str__(self):
        return f"{self.nome} ({self.formatar_quantidade})"

    @property
    def formatar_quantidade(self):
        q = self.quantidade_total
        if self.unidade_base == "g":
            kg = int(q // 1000)
            g = q % 1000
            return f"{kg} kg {int(g)} g" if kg else f"{int(g)} g"
        elif self.unidade_base == "ml":
            l = int(q // 1000)
            ml = q % 1000
            return f"{l} L {int(ml)} ml" if l else f"{int(ml)} ml"
        else:
            return f"{int(q)} un"


# ------------------ SAÍDA DE INSUMO ------------------

class SaidaInsumo(models.Model):
    UNIDADES = [
        ("g", "Grama(s)"),
        ("ml", "Mililitro(s)"),
        ("un", "Unidade(s)")
    ]
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    colaborador_entregando = models.ForeignKey(
        Colaborador, on_delete=models.CASCADE, related_name='entregas')
    colaborador_retira = models.ForeignKey(
        Colaborador, on_delete=models.CASCADE, related_name='retiradas')
    quantidade_principal = models.FloatField(default=0)
    quantidade_complementar = models.FloatField(default=0)
    unidade = models.CharField(max_length=5, choices=UNIDADES, default="un")
    data = models.DateTimeField(auto_now_add=True)

    def total_em_unidade_base(self):
        total = self.quantidade_principal
        if self.unidade in ['g', 'ml', 'un']:
            total += self.quantidade_complementar
        return total

    @property
    def quantidade_total(self):
        if self.unidade in ['g', 'ml']:
            return self.quantidade_principal * 1000 + self.quantidade_complementar
        else:
            return self.quantidade_principal + self.quantidade_complementar

    @property
    def exibir_quantidade(self):
        total = self.quantidade_total
        if self.unidade == 'g':
            return f"{int(total/1000)} kg" if total >= 1000 else f"{int(total)} g"
        elif self.unidade == 'ml':
            return f"{int(total/1000)} L" if total >= 1000 else f"{int(total)} ml"
        else:
            return f"{int(total)} un"

    def __str__(self):
        return f"{self.exibir_quantidade} de {self.insumo.nome}"


# ------------------ FICHA DE PRODUÇÃO ------------------

class FichaProducao(models.Model):
    produto = models.ForeignKey(ProdutoPronto, on_delete=models.CASCADE)
    colaborador = models.ForeignKey(
        Colaborador, on_delete=models.SET_NULL, null=True, blank=True)
    categoria = models.CharField(max_length=100)
    data_fabricacao = models.DateField()
    textura = models.CharField(max_length=255, blank=True, null=True)
    validade = models.PositiveIntegerField(default=3)
    armazenamento = models.CharField(max_length=255, blank=True, null=True)
    calorias = models.PositiveIntegerField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    tempo_preparo = models.PositiveIntegerField(
        "Tempo de Preparo (minutos)", blank=True, null=True)
    perda_aceitavel = models.CharField(
        "Perda Aceitável", max_length=50, blank=True)
    rendimento = models.CharField(
        "Rendimento", max_length=100, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    assinado_por = models.CharField(max_length=150, blank=True, null=True)
    data_assinatura = models.DateTimeField(blank=True, null=True)
    peso_produto = models.FloatField(
        default=0, help_text="Peso do produto em gramas")

    def __str__(self):
        return f"Ficha de Produção - {self.id}"


class FichaInsumo(models.Model):
    ficha = models.ForeignKey(
        FichaProducao, on_delete=models.CASCADE, related_name='ficha_insumos')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    quantidade_usada = models.FloatField()
    unidade = models.CharField(
        max_length=10, choices=Insumo._meta.get_field('unidade_base').choices)

    def __str__(self):
        return f"{self.insumo.nome} - {self.quantidade_usada}{self.unidade}"


# ------------------ PRODUTO VENDA (PDV) ------------------

class ProdutoVenda(models.Model):

    produto_pronto = models.ForeignKey(
        ProdutoPronto,
        on_delete=models.PROTECT,
        related_name="vendas"
    )

    codigo_externo = models.CharField(
        max_length=20,
        unique=True
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo_externo} - R$ {self.preco}"


# ------------------ PEDIDO / VENDA ------------------

class Pedido(models.Model):

    produto_venda = models.ForeignKey(
        ProdutoVenda,
        on_delete=models.PROTECT
    )

    quantidade = models.IntegerField()

    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    data = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    def save(self, *args, **kwargs):

        self.valor_unitario = self.produto_venda.preco
        self.valor_total = self.quantidade * self.valor_unitario

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.id} - {self.produto_venda}"
