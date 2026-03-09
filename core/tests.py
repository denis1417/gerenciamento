from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
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
# TESTE DE PRODUTO
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
# TESTE DE ESTOQUE BAIXO
# ======================================================

class InsumoEstoqueTestCase(TestCase):

    def setUp(self):
        self.insumo = Insumo.objects.create(
            nome="Farinha",
            quantidade_total=5
        )

    def test_estoque_baixo(self):
        estoque_baixo = Insumo.objects.filter(quantidade_total__lt=10)
        self.assertEqual(estoque_baixo.count(), 1)
        self.assertEqual(estoque_baixo.first().nome, "Farinha")

# ======================================================
# TESTE DA VIEW DO DASHBOARD
# ======================================================


class DashboardTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='teste',
            password='123456'
        )
        self.client.login(username='teste', password='123456')

    def test_dashboard_carrega(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_template(self):
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'core/dashboard.html')
