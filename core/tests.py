from django.test import TestCase
from core.models import Colaborador, Produto, Insumo
from datetime import date


# ======================================================
# TESTE DE COLABORADOR
# ======================================================

class ColaboradorTestCase(TestCase):

    def setUp(self):
        self.colaborador = Colaborador.objects.create(
            rc="RC001",
            nome="Funcionario Teste",
            data_nascimento=date(2000, 1, 1),
            sexo="M",
            funcao="Atendente",
            CPF_RG="12345678900"
        )

    def test_colaborador_criado(self):
        self.assertEqual(self.colaborador.nome, "Funcionario Teste")

    def test_rc_colaborador(self):
        self.assertEqual(self.colaborador.rc, "RC001")

    def test_funcao_colaborador(self):
        self.assertEqual(self.colaborador.funcao, "Atendente")


# ======================================================
# TESTE DE PRODUTO (EXIGIDO NO PDF)
# ======================================================

class ProdutoTestCase(TestCase):

    def setUp(self):
        self.produto = Produto.objects.create(
            codigo="P001",
            nome="Bolo Teste",
            categoria="Bolos",
            data_fabricacao=date.today(),
            data_validade=date.today(),
            quantidade=10
        )

    def test_produto_criado(self):
        self.assertEqual(self.produto.nome, "Bolo Teste")

    def test_quantidade_produto(self):
        self.assertEqual(self.produto.quantidade, 10)


# ======================================================
# TESTE DE ESTOQUE BAIXO (EXIGIDO NO PDF)
# ======================================================

class InsumoEstoqueTestCase(TestCase):

    def setUp(self):
        self.insumo = Insumo.objects.create(
            nome="Farinha",
            quantidade_total=5
        )

    def test_estoque_baixo(self):
        estoque_baixo = Insumo.objects.filter(quantidade_total__lt=10)
        self.assertTrue(self.insumo in estoque_baixo)


# Create your tests here.
