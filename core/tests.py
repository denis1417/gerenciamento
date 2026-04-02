from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Colaborador, Insumo, Produto, VistoriaInsumo, CatalogoProduto, ProdutoVenda, ProdutoPronto, Pedido

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


# ======================================================
# TESTE DO RELATÓRIO DE INSUMOS (POST CHECKLIST)
# ======================================================

class RelatorioInsumosPostTestCase(TestCase):

    def setUp(self):
        # usuário
        self.user = User.objects.create_user(
            username='teste',
            password='123456'
        )

        # login
        self.client.login(username='teste', password='123456')

        # insumos
        self.insumo1 = Insumo.objects.create(
            nome="Farinha",
            quantidade_total=5000,
            unidade_base="g"
        )

        self.insumo2 = Insumo.objects.create(
            nome="Açúcar",
            quantidade_total=3000,
            unidade_base="g"
        )

    def test_salvar_checklist(self):

        data = {
            f"real_{self.insumo1.id}": "4500",
            f"real_{self.insumo2.id}": "2800",
        }

        response = self.client.post(
            reverse('relatorio_insumos'),
            data
        )

        # verifica resposta
        self.assertIn(response.status_code, [200, 302])

        # verifica se salvou
        self.assertEqual(VistoriaInsumo.objects.count(), 2)

        vistoria1 = VistoriaInsumo.objects.get(insumo=self.insumo1)
        self.assertEqual(vistoria1.quantidade_real, 4500)

        vistoria2 = VistoriaInsumo.objects.get(insumo=self.insumo2)
        self.assertEqual(vistoria2.quantidade_real, 2800)


class ProdutoAPITestCase(APITestCase):

    def setUp(self):
        # cria usuário
        self.user = User.objects.create_user(
            username='apiuser',
            password='123456'
        )

        # autentica na API
        self.client.force_authenticate(user=self.user)

        # cria produto inicial
        self.produto = Produto.objects.create(
            codigo="P002",
            nome="Bolo API",
            categoria="Bolos",
            data_fabricacao=date.today(),
            data_validade=date.today(),
            quantidade=5
        )

    # =========================
    # GET
    # =========================
    def test_listar_produtos(self):
        response = self.client.get('/api/produtos/')
        self.assertEqual(response.status_code, 200)

    # =========================
    # POST
    # =========================
    def test_criar_produto(self):
        data = {
            "codigo": "P003",
            "nome": "Torta API",
            "categoria": "Doces",
            "data_fabricacao": str(date.today()),
            "data_validade": str(date.today()),
            "quantidade": 10
        }

        response = self.client.post('/api/produtos/', data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Produto.objects.count(), 2)

    # =========================
    # PUT (update completo)
    # =========================
    def test_atualizar_produto(self):
        url = f'/api/produtos/{self.produto.id}/'

        data = {
            "codigo": "P002",
            "nome": "Bolo Atualizado",
            "categoria": "Bolos",
            "data_fabricacao": str(self.produto.data_fabricacao),
            "data_validade": str(self.produto.data_validade),
            "quantidade": 20
        }

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, 200)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.nome, "Bolo Atualizado")
        self.assertEqual(self.produto.quantidade, 20)

    # =========================
    # PATCH (update parcial)
    # =========================
    def test_atualizar_parcial_produto(self):
        url = f'/api/produtos/{self.produto.id}/'

        data = {
            "nome": "Bolo PATCH"
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, 200)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.nome, "Bolo PATCH")

    # =========================
    # DELETE
    # =========================
    def test_deletar_produto(self):
        url = f'/api/produtos/{self.produto.id}/'

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Produto.objects.count(), 0)


class PedidoFluxoTestCase(APITestCase):

    def setUp(self):
        from core.models import CatalogoProduto, ProdutoVenda, ProdutoPronto
        from datetime import date

        # 1. Usuário Admin
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            password='password123',
            email='admin@teste.com'
        )

        # 2. Catálogo (Apenas nome e descrição conforme seu model)
        self.catalogo = CatalogoProduto.objects.create(
            nome="Bolo de Chocolate",
            descricao="Bolo fofinho"
        )

        # 3. Lotes (Preenchendo data_fabricacao e data_validade que são obrigatórios)
        hoje = date.today()
        self.lote_antigo = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=hoje,
            data_validade=date(2026, 5, 1),
            peso_produto=500.0
        )

        self.lote_novo = ProdutoPronto.objects.create(
            catalogo=self.catalogo,
            quantidade=10,
            data_fabricacao=hoje,
            data_validade=date(2026, 12, 1),
            peso_produto=500.0
        )

        # 4. Produto Venda (Precisa do codigo_externo único e preco decimal)
        self.produto_venda = ProdutoVenda.objects.create(
            produto_pronto=self.lote_antigo,
            codigo_externo="BOLO-001",  # Campo obrigatório no seu model
            preco=50.00,
            ativo=True
        )

    def test_criar_pedido_baixa_estoque_fifo(self):
        """Testa se a CriarPedidoView reduz o estoque do lote mais antigo primeiro"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('api_pedidos_criar')

        # O campo esperado no POST deve ser 'produto' (ID do ProdutoVenda) e 'quantidade'
        data = {'produto': self.produto_venda.id, 'quantidade': 12}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        # Recarregar lotes para ver se a baixa funcionou
        self.lote_antigo.refresh_from_db()
        self.lote_novo.refresh_from_db()

        # Se a lógica FIFO estiver certa:
        # Lote antigo (10) deve zerar. Lote novo (10) deve cair para 8.
        self.assertEqual(self.lote_antigo.quantidade, 0)
        self.assertEqual(self.lote_novo.quantidade, 8)

    def test_listar_pedidos_acesso_admin(self):
        """Testa se a nova URL de listagem funciona para admins"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('api_pedidos_listar')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_criar_pedido_estoque_insuficiente(self):
        """Testa se bloqueia pedido maior que o estoque total (20 unidades)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('api_pedidos_criar')

        data = {'produto': self.produto_venda.id, 'quantidade': 25}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn("Estoque insuficiente", response.data['erro'])
