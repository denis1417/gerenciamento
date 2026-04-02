from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Colaborador, Produto, Insumo
from datetime import date
from core.models import Colaborador, Produto, Insumo, VistoriaInsumo
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Produto
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
