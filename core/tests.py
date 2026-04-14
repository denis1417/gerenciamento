from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import (
    Colaborador, Insumo, Produto, VistoriaInsumo,
    CatalogoProduto, ProdutoVenda, ProdutoPronto, Pedido
)

# ======================================================
# COLABORADOR
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


# ======================================================
# PRODUTO
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


# ======================================================
# INSUMO
# ======================================================

class InsumoEstoqueTestCase(TestCase):

    def setUp(self):
        self.insumo = Insumo.objects.create(
            nome="Farinha",
            quantidade_total=5
        )

    def test_estoque_baixo(self):
        self.assertTrue(self.insumo.quantidade_total < 10)


# ======================================================
# DASHBOARD BÁSICO
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


# ======================================================
# DASHBOARD BUSINESS (MÉTRICAS + PERDAS)
# ======================================================

class DashboardBusinessTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='dash',
            password='123456'
        )
        self.client.login(username='dash', password='123456')

        self.catalogo = CatalogoProduto.objects.create(nome="Bolo Teste")

        hoje = date.today()

        self.lote_vencido = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=5,
            data_fabricacao=hoje,
            data_validade=hoje - timedelta(days=1),
            peso_produto=1
        )

        self.lote_ok = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=hoje,
            data_validade=hoje + timedelta(days=10),
            peso_produto=1
        )

        self.produto_venda = ProdutoVenda.objects.create(
            produto_pronto=self.lote_ok,
            codigo_externo="DASH001",
            preco=20,
            ativo=True
        )

        Pedido.objects.create(
            produto_venda=self.produto_venda,
            quantidade=2,
            valor_unitario=20,
            valor_total=40,
            usuario=self.user
        )

    def test_dashboard_metrics(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        context = response.context

        self.assertIn("perda_financeira", context)
        self.assertIn("ticket_medio", context)
        self.assertIn("total_itens_vencidos", context)

        self.assertGreaterEqual(context["ticket_medio"], 0)
        self.assertGreaterEqual(context["perda_financeira"], 0)


# ======================================================
# RELATÓRIO INSUMOS
# ======================================================

class RelatorioInsumosPostTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='teste',
            password='123456'
        )
        self.client.login(username='teste', password='123456')

        self.insumo = Insumo.objects.create(
            nome="Farinha",
            quantidade_total=5000,
            unidade_base="g"
        )

    def test_salvar_checklist(self):
        data = {f"real_{self.insumo.id}": "4500"}

        response = self.client.post(
            reverse('relatorio_insumos'),
            data
        )

        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(VistoriaInsumo.objects.count(), 1)


# ======================================================
# API PRODUTO
# ======================================================

class ProdutoAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            password='123456'
        )
        self.client.force_authenticate(user=self.user)

        self.catalogo = CatalogoProduto.objects.create(
            nome="Produto API"
        )

        self.lote = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=date.today(),
            data_validade=date.today() + timedelta(days=10),
            peso_produto=1.0
        )

        self.produto_venda = ProdutoVenda.objects.create(
            produto_pronto=self.lote,
            codigo_externo="API001",
            preco=10,
            ativo=True
        )

        # ⚠️ Produto SEM catalogo (corrigido)
        self.produto = Produto.objects.create(
            codigo="P002",
            nome="Bolo API",
            categoria="Bolos",
            data_fabricacao=date.today(),
            data_validade=date.today(),
            quantidade=5
        )

    def test_listar_produtos(self):
        response = self.client.get('/api/produtos/')
        self.assertEqual(response.status_code, 200)

    def test_delete_produto(self):
        url = f'/api/produtos/{self.produto.pk}/'

        response = self.client.delete(url)

        self.assertIn(response.status_code, [204, 405])

    def test_api_produtos_listagem(self):
        response = self.client.get('/api/produtos/')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_api_produtos_criacao(self):
        data = {
            "codigo": "TESTE123",
            "nome": "Produto Teste API",
            "categoria": "Bolos",
            "data_fabricacao": str(date.today()),
            "data_validade": str(date.today()),
            "quantidade": 5
        }

        response = self.client.post('/api/produtos/', data)

        self.assertIn(response.status_code, [200, 201])

        self.assertIn("nome", response.json())
# ======================================================
# FIFO / PEDIDOS
# ======================================================


class PedidoFluxoTestCase(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            password='123456'
        )

        self.catalogo = CatalogoProduto.objects.create(nome="Bolo")

        hoje = date.today()

        self.lote1 = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=hoje,
            data_validade=hoje + timedelta(days=1),
            peso_produto=1
        )

        self.lote2 = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=hoje,
            data_validade=hoje + timedelta(days=10),
            peso_produto=1
        )

        self.produto_venda = ProdutoVenda.objects.create(
            produto_pronto=self.lote1,
            codigo_externo="TESTE",
            preco=10,
            ativo=True
        )

    def test_criar_pedido(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse('api_pedidos_criar'),
            {"produto": self.produto_venda.id, "quantidade": 2}
        )

        self.assertEqual(response.status_code, 201)

        pedido = Pedido.objects.first()
        self.assertEqual(float(pedido.valor_total), 20.0)


# ======================================================
# VENDAS API
# ======================================================

class VendaAPITestCase(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin2',
            password='123456'
        )

    def test_acesso_api(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get('/api/vendas/')
        self.assertIn(response.status_code, [200, 405])
