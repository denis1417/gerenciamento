# =========================================================
# PDF PROFISSIONAL - REPORTLAB PLATYPUS
# =========================================================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from django.conf import settings
import os
from django.http import HttpResponse
from .models import Produto, Insumo, Colaborador
from datetime import datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import ProdutoSerializer, InsumoSerializer, ColaboradorSerializer
from .models import Produto, Insumo, Colaborador

from collections import defaultdict
from datetime import date, timedelta
from django.db.models import Count

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Avg, F, FloatField
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.contrib.auth.models import User, Group
import json

from .decorators import check_group
from .models import (
    Colaborador,
    Produto,
    ProdutoPronto,
    FichaProducao,
    FichaInsumo,
    SaidaInsumo,
    Insumo,
    CatalogoProduto,
    VistoriaInsumo  # adicionado
)
from .forms import (
    ProdutoProntoForm,
    FichaProducaoForm,
    InsumoForm,
    SaidaInsumoForm,
    ColaboradorForm
)


# =========================================================
# LOGIN / LOGOUT
# =========================================================


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:

            login(request, user)

            if user.is_superuser or user.groups.filter(name="Administrador").exists():
                return redirect("home")

            elif user.groups.filter(name="RH").exists():
                return redirect("colaboradores_list")

            elif user.groups.filter(name="Insumos").exists():
                return redirect("insumos_list")

            elif user.groups.filter(name="Confeitaria").exists():
                return redirect("produtos_list")

            else:
                return redirect("home")

        else:
            messages.error(request, "Usuário ou senha incorretos.")

    users_exist = User.objects.exists()

    return render(request, "core/login.html", {"users_exist": users_exist})


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# HOME
# =========================================================

@login_required
def home(request):

    colaborador = None
    if hasattr(request.user, 'colaborador'):
        colaborador = request.user.colaborador

    context = {
        "colaborador": colaborador,
        "is_admin": request.user.is_superuser or request.user.groups.filter(name="Administrador").exists(),
        "is_rh": request.user.groups.filter(name="RH").exists() or request.user.is_superuser,
        "is_insumo": request.user.groups.filter(name="Insumos").exists() or request.user.is_superuser,
        "is_confeitaria": request.user.groups.filter(name="Confeitaria").exists() or request.user.is_superuser,
    }

    return render(request, "core/home.html", context)
# =========================================================
# COLABORADORES
# =========================================================


@login_required
@check_group("RH")
def colaboradores_list(request):
    query = request.GET.get('q')
    if query:
        colaboradores = Colaborador.objects.filter(
            nome__icontains=query).order_by('nome')
    else:
        colaboradores = Colaborador.objects.all().order_by('nome')
    return render(request, "core/colaboradores_list.html", {"colaboradores": colaboradores})


@login_required
@check_group("RH")
def colaboradores_create(request):
    form = ColaboradorForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            colaborador = form.save()
            messages.success(
                request, f"Colaborador {colaborador.nome} cadastrado com sucesso!")
            return redirect("colaboradores_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return render(request, "core/form_colaborador.html", {"form": form, "titulo": "Cadastrar Colaborador"})


@login_required
@check_group("RH")
def colaboradores_edit(request, id):
    colaborador = get_object_or_404(Colaborador, id=id)
    form = ColaboradorForm(request.POST or None,
                           request.FILES or None, instance=colaborador)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, f"Colaborador {colaborador.nome} atualizado com sucesso!")
        return redirect("colaboradores_list")
    return render(request, "core/form_colaborador.html", {"form": form, "titulo": "Editar Colaborador"})


@login_required
@check_group("RH")
def colaboradores_delete(request, id):
    colaborador = get_object_or_404(Colaborador, id=id)
    if request.method == "POST":
        colaborador.delete()
        messages.success(
            request, f"Colaborador {colaborador.nome} deletado com sucesso!")
        return redirect("colaboradores_list")
    return render(request, "core/delete.html", {"obj": colaborador})


@login_required
@check_group("RH")
def colaboradores_detail(request, id):
    colaborador = get_object_or_404(Colaborador, id=id)
    return render(request, "core/colaboradores_detail.html", {"colaborador": colaborador})


# =========================================================
# USUÁRIOS
# =========================================================

@login_required
@check_group("Administrador")
def usuarios_create(request):
    colaboradores = Colaborador.objects.all().order_by("nome")
    if request.method == "POST":
        username = request.POST.get("username")
        senha_nova = request.POST.get("senha_nova")
        senha_confirmacao = request.POST.get("senha_confirmacao")
        senha_admin = request.POST.get("senha_admin")
        grupo = request.POST.get("grupo")
        colaborador_id = request.POST.get("colaborador")

        if not check_password(senha_admin, request.user.password):
            messages.error(request, "Senha de administrador incorreta.")
        elif senha_nova != senha_confirmacao:
            messages.error(request, "As senhas não coincidem.")
        elif not colaborador_id:
            messages.error(request, "Selecione um colaborador.")
        else:
            colaborador = get_object_or_404(Colaborador, id=colaborador_id)
            user = User.objects.create_user(
                username=username, password=senha_nova)
            if grupo:
                grupo_obj, _ = Group.objects.get_or_create(name=grupo)
                user.groups.add(grupo_obj)
            colaborador.usuario = user
            colaborador.save()
            messages.success(
                request, f"Usuário {username} cadastrado com sucesso!")
            return redirect("criar_usuario")
    return render(request, "core/criar_usuario.html", {"colaboradores": colaboradores})


@login_required
@check_group("Administrador")
def usuarios_list(request):
    usuarios = User.objects.all().order_by("username")
    return render(request, "core/usuarios_list.html", {"usuarios": usuarios})


@login_required
@check_group("Administrador")
def usuario_delete(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == "POST":
        user.delete()
        messages.success(
            request, f"Usuário {user.username} deletado com sucesso!")
        return redirect("listar_usuarios")
    return render(request, "core/delete.html", {"obj": user})


# =========================================================
# INSUMOS
# =========================================================

@login_required
@check_group("Insumos")
def insumos_list(request):
    insumos = Insumo.objects.all()
    return render(request, "core/insumos_list.html", {"insumos": insumos})


@login_required
@check_group("Insumos")
def insumos_create(request):
    form = InsumoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Insumo cadastrado com sucesso!")
        return redirect("insumos_list")
    return render(request, "core/form.html", {"form": form, "titulo": "Cadastrar Insumo"})


@login_required
@check_group("Insumos")
def insumos_edit(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    form = InsumoForm(request.POST or None, instance=insumo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Insumo atualizado com sucesso!")
        return redirect("insumos_list")
    return render(request, "core/form.html", {"form": form, "titulo": "Editar Insumo"})


@login_required
@check_group("Insumos")
def insumos_delete(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    if request.method == "POST":
        insumo.delete()
        return redirect("insumos_list")
    return render(request, "core/delete.html", {"obj": insumo})


# =========================================================
# SAÍDA DE INSUMOS
# =========================================================

@login_required
@check_group("Insumos")
def saida_insumo_list(request):
    saidas = SaidaInsumo.objects.all().order_by("-data")
    return render(request, "core/saida_insumo_list.html", {"saidas": saidas})


@login_required
@check_group("Insumos")
def saida_insumo_create(request):
    form = SaidaInsumoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        saida = form.save(commit=False)
        insumo = saida.insumo

        # Pega a quantidade digitada
        quantidade = form.cleaned_data.get('quantidade') or 0

        if quantidade == 0:
            messages.error(request, "Você precisa informar a quantidade.")
            return redirect(request.path)

        if quantidade > insumo.quantidade_total:
            messages.error(
                request,
                f"A quantidade solicitada ({quantidade} {insumo.unidade_base}) "
                f"excede o estoque disponível ({insumo.quantidade_total} {insumo.unidade_base})."
            )
            return redirect(request.path)

        # Atualiza o estoque
        insumo.quantidade_total -= quantidade
        insumo.save()

        # Salva a saída no modelo
        saida.quantidade_principal = quantidade
        saida.quantidade_complementar = 0  # zera complementar
        saida.save()

        messages.success(request, "Saída de insumo registrada com sucesso.")
        return redirect("saida_insumo_list")

    return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})


@login_required
@check_group("Insumos")
def saida_insumo_delete(request, id):
    """
    Deleta uma saída de insumo e devolve a quantidade retirada ao insumo original.
    """
    saida = get_object_or_404(SaidaInsumo, pk=id)
    insumo = saida.insumo

    if request.method == "POST":
        # Recupera a quantidade total em unidade base
        quantidade_devolvida = saida.quantidade_total
        # Atualiza o estoque do insumo
        insumo.quantidade_total += quantidade_devolvida
        insumo.save()

        # Deleta a saída
        saida.delete()
        messages.success(
            request, f"Saída de {insumo.nome} removida com sucesso e estoque atualizado.")
        # ajuste para a sua URL de listagem de saídas
        return redirect('saida_insumo_list')

    return render(request, "core/saida_insumo_confirm_delete.html", {"saida": saida})

# =========================================================
# PRODUTOS
# =========================================================

# -------------------- LISTA DE PRODUTOS --------------------


@login_required
@check_group("Confeitaria")
def produtos_list(request):
    """
    Exibe todos os produtos prontos cadastrados.
    Acesso: grupo Confeitaria e Administrador.
    """
    produtos = ProdutoPronto.objects.select_related('catalogo').all()

    for p in produtos:
        # Verifica se há ficha de produção associada
        ficha = FichaProducao.objects.filter(produto=p).first()
        p.ficha_existe = bool(ficha)
        p.ficha = ficha

        # Define classe CSS conforme a validade
        if p.data_validade:
            if p.data_validade < date.today():
                p.row_class = "produto-vencido"
            elif p.data_validade == date.today():
                p.row_class = "produto-hoje"
            elif p.data_validade <= date.today() + timedelta(days=3):
                p.row_class = "produto-proximo"
            else:
                p.row_class = ""
        else:
            p.row_class = ""

    return render(request, "core/produtos_list.html", {"produtos": produtos})


# -------------------- CADASTRAR PRODUTO --------------------
@login_required
@check_group("Confeitaria")
def produtos_create(request):
    """
    Permite o cadastro de novos produtos prontos.
    Acesso: grupo Confeitaria e Administrador.
    """
    form = ProdutoProntoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produto = form.save()
        messages.success(
            request, f"Produto {produto.catalogo.nome} cadastrado com sucesso!")
        return redirect("produtos_list")

    return render(request, "core/form.html", {"form": form, "titulo": "Cadastrar Produto"})


# -------------------- EDITAR PRODUTO --------------------
@login_required
@check_group("Confeitaria")
def produtos_edit(request, id):
    """
    Edita um produto existente.
    Acesso: grupo Confeitaria e Administrador.
    """
    produto = get_object_or_404(ProdutoPronto, id=id)
    form = ProdutoProntoForm(request.POST or None, instance=produto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, f"Produto {produto.catalogo.nome} atualizado com sucesso!")
        return redirect("produtos_list")

    return render(request, "core/form.html", {"form": form, "titulo": f"Editar Produto: {produto.catalogo.nome}"})


# -------------------- EXCLUIR PRODUTO --------------------
@login_required
@check_group("Confeitaria")
def produtos_delete(request, id):
    """
    Exclui um produto existente.
    Acesso: grupo Confeitaria e Administrador.
    """
    produto = get_object_or_404(ProdutoPronto, id=id)
    if request.method == "POST":
        nome_produto = produto.catalogo.nome
        produto.delete()
        messages.success(
            request, f"Produto {nome_produto} excluído com sucesso!")
        return redirect("produtos_list")

    return render(request, "core/confirm_delete.html", {"obj": produto})


@login_required
def relatorio_insumos(request):
    """
    Exibe relatório de insumos com:
    - Quantidade retirada (Saída de Insumos)
    - Quantidade usada (FichaInsumo)
    - Quantidade teórica (retirado - usado)
    Permite registrar vistoria (checklist) e salvar histórico.
    """
    relatorio = []
    insumos = Insumo.objects.all()

    for insumo in insumos:
        # Calcula quantidade retirada
        saida_qs = SaidaInsumo.objects.filter(insumo=insumo)
        soma_principal = saida_qs.aggregate(
            total=Sum('quantidade_principal'))['total'] or 0
        soma_complementar = saida_qs.aggregate(
            total=Sum('quantidade_complementar'))['total'] or 0
        retirado = float(soma_principal) + float(soma_complementar)

        # Calcula quantidade usada em fichas
        usado = float(FichaInsumo.objects.filter(insumo=insumo).aggregate(
            total=Sum('quantidade_usada')
        )['total'] or 0)

        # Calcula teórico
        teorico = max(retirado - usado, 0)

        relatorio.append({
            'insumo': insumo,
            'retirado': retirado,
            'usado': usado,
            'teorico': teorico,
        })

    # Salvar checklist / vistoria
    if request.method == "POST":
        for item in relatorio:
            real_str = request.POST.get(f"real_{item['insumo'].id}", "")
            if not real_str:
                continue
            try:
                real = float(real_str)
            except ValueError:
                continue  # Ignora valores inválidos
            desperdicio = item['teorico'] - real

            VistoriaInsumo.objects.create(
                insumo=item['insumo'],
                quantidade_retirada=item['retirado'],
                quantidade_usada=item['usado'],
                quantidade_teorica=item['teorico'],
                quantidade_real=real,
                desperdicio=desperdicio,
                data_vistoria=date.today(),
            )

        messages.success(request, "✅ Vistoria registrada com sucesso!")
        return redirect('relatorio_insumos')

    # Histórico de checklists agrupados por data
    checklists = VistoriaInsumo.objects.values(
        'data_vistoria'
    ).distinct().order_by('-data_vistoria')

    context = {
        'relatorio': relatorio,
        'checklists': checklists,
    }

    return render(request, 'core/relatorio_insumos.html', context)


@login_required
def visualizar_checklist(request, data_vistoria):
    """
    Visualiza checklist de uma vistoria específica com opção de impressão.
    """
    itens = VistoriaInsumo.objects.filter(data_vistoria=data_vistoria)
    return render(request, 'core/checklist_vistoria.html', {
        'itens': itens,
        'data_vistoria': data_vistoria
    })


@login_required
@check_group(["Administrador", "Insumos"])
def excluir_checklist(request, data_vistoria):
    if request.method == "POST":
        VistoriaInsumo.objects.filter(data_vistoria=data_vistoria).delete()
        messages.success(request, "Checklist excluído com sucesso!")
    return redirect('relatorio_insumos')


@login_required
@check_group(["Administrador", "Confeitaria"])
def criar_ficha(request):
    produtos_list = ProdutoPronto.objects.all()
    colaborador_logado = None if request.user.is_superuser else Colaborador.objects.filter(
        usuario=request.user).first()

    # Produto selecionado via GET ou POST
    produto_id = request.GET.get("produto") or request.POST.get("produto")
    produto = get_object_or_404(
        ProdutoPronto, id=produto_id) if produto_id else None

    # Insumos disponíveis (soma principal + complementar > 0)
    insumos_disponiveis = SaidaInsumo.objects.filter(
        Q(quantidade_principal__gt=0) | Q(quantidade_complementar__gt=0)
    ).select_related("insumo")

    # Inicializa formulário com peso do produto, se existir
    initial_data = {"peso_produto": produto.peso_produto} if produto else {}
    form = FichaProducaoForm(request.POST or None, initial=initial_data)

    if request.method == "POST":
        # Verifica senha
        senha = request.POST.get("senha_confirmacao")
        user = authenticate(username=request.user.username, password=senha)
        if user is None:
            messages.error(request, "Senha incorreta. Tente novamente.")
            return redirect(request.path)

        if not produto:
            messages.error(request, "Selecione um produto.")
            return redirect(request.path)

        if form.is_valid():
            ficha = form.save(commit=False)
            ficha.produto = produto
            ficha.peso_produto = produto.peso_produto  # garante o peso cadastrado
            ficha.assinado_por = colaborador_logado.nome if colaborador_logado else request.user.username
            ficha.data_assinatura = timezone.now()
            ficha.colaborador = colaborador_logado
            ficha.save()

            # Registrar insumos usados
            insumos_ids = request.POST.getlist("insumo_id[]")
            quantidades = request.POST.getlist("quantidade_usada[]")
            unidades = request.POST.getlist("unidade[]")

            for i, insumo_id in enumerate(insumos_ids):
                if insumo_id and quantidades[i]:
                    insumo_saida = get_object_or_404(SaidaInsumo, id=insumo_id)
                    quantidade_usada = float(quantidades[i])
                    unidade = unidades[i]

                    # Cria registro na ficha
                    FichaInsumo.objects.create(
                        ficha=ficha,
                        insumo=insumo_saida.insumo,
                        quantidade_usada=quantidade_usada,
                        unidade=unidade
                    )

                    # Calcula total disponível
                    total_disponivel = insumo_saida.quantidade_principal + \
                        insumo_saida.quantidade_complementar
                    restante = total_disponivel - quantidade_usada

                    # Ajusta principal e complementar proporcionalmente ou zera
                    if restante >= 0:
                        if quantidade_usada <= insumo_saida.quantidade_principal:
                            insumo_saida.quantidade_principal -= quantidade_usada
                        else:
                            insumo_saida.quantidade_complementar = max(
                                restante, 0)
                            insumo_saida.quantidade_principal = 0
                    else:
                        insumo_saida.quantidade_principal = 0
                        insumo_saida.quantidade_complementar = 0

                    insumo_saida.save()

            messages.success(request, "Ficha criada e assinada com sucesso!")
            return redirect("visualizar_ficha", ficha_id=ficha.id)

    context = {
        "form": form,
        "produtos_list": produtos_list,
        "insumos_disponiveis": insumos_disponiveis,
        "produto": produto,
        "colaborador_logado": colaborador_logado,
        "usuario_logado": request.user,
    }
    return render(request, "core/ficha_form.html", context)


@login_required
def visualizar_ficha(request, ficha_id):
    ficha = get_object_or_404(FichaProducao, id=ficha_id)
    ficha_insumos = ficha.ficha_insumos.all()
    return render(request, "core/ficha_detalhada.html", {"ficha": ficha, "ficha_insumos": ficha_insumos})


@login_required
@check_group("Confeitaria")
def fichas_list(request):
    fichas = FichaProducao.objects.select_related(
        "produto", "colaborador").order_by("-data_assinatura")
    return render(request, "core/fichas_list.html", {"fichas": fichas})


@login_required
@check_group("Confeitaria")
def editar_ficha(request, id):
    ficha = get_object_or_404(FichaProducao, id=id)
    form = FichaProducaoForm(request.POST or None, instance=ficha)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ficha de produção atualizada com sucesso!")
        return redirect("fichas_list")
    return render(request, "core/form.html", {"form": form, "titulo": "Editar Ficha de Produção"})


@login_required
@check_group("Confeitaria")
def deletar_ficha(request, id):
    ficha = get_object_or_404(FichaProducao, id=id)
    if request.method == "POST":
        ficha.delete()
        messages.success(request, "Ficha de produção deletada com sucesso!")
        return redirect("fichas_list")
    return render(request, "core/delete.html", {"obj": ficha})


@login_required
@check_group("Administrador")
def catalogo_list(request):
    catalogo = CatalogoProduto.objects.all()
    return render(request, "core/catalogo_list.html", {"catalogo": catalogo})


@login_required
@check_group("Administrador")
def catalogo_create(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        CatalogoProduto.objects.create(nome=nome, descricao=descricao)
        messages.success(request, "Produto adicionado ao catálogo!")
        return redirect("catalogo_list")
    return render(request, "core/catalogo_form.html")


@login_required
@check_group("Administrador")
def catalogo_edit(request, pk):
    catalogo_item = get_object_or_404(CatalogoProduto, id=pk)
    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        catalogo_item.nome = nome
        catalogo_item.descricao = descricao
        catalogo_item.save()
        messages.success(request, "Produto atualizado com sucesso!")
        return redirect("catalogo_list")
    return render(request, "core/catalogo_form.html", {"catalogo": catalogo_item})


@login_required
@check_group("Administrador")
def catalogo_delete(request, id):
    item = get_object_or_404(CatalogoProduto, id=id)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Produto do catálogo deletado!")
        return redirect("catalogo_list")
    return render(request, "core/delete.html", {"obj": item})


@login_required
def dashboard(request):

    colaborador = None
    if hasattr(request.user, 'colaborador'):
        colaborador = request.user.colaborador

    total_produtos = Produto.objects.aggregate(
        total=Count('id')
    )['total'] or 0

    total_insumos = Insumo.objects.aggregate(
        total=Count('id')
    )['total'] or 0

    total_colaboradores = Colaborador.objects.aggregate(
        total=Count('id')
    )['total'] or 0

    estoque_baixo = Insumo.objects.filter(
        quantidade_total__lt=10
    ).order_by('quantidade_total')

    context = {
        'colaborador': colaborador,
        'total_produtos': total_produtos,
        'total_insumos': total_insumos,
        'total_colaboradores': total_colaboradores,
        'estoque_baixo': estoque_baixo,
    }

    return render(request, 'core/dashboard.html', context)

# =====================================================
# API REST VIEWSETS
# =====================================================


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    API para gerenciamento de Produtos.
    Apenas usuários autenticados podem acessar.
    """
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]


class InsumoViewSet(viewsets.ModelViewSet):
    """
    API para gerenciamento de Insumos.
    Apenas usuários autenticados podem acessar.
    """
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer
    permission_classes = [IsAuthenticated]


class ColaboradorViewSet(viewsets.ModelViewSet):
    """
    API para gerenciamento de Colaboradores.
    Apenas usuários autenticados podem acessar.
    """
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    permission_classes = [IsAuthenticated]


# =========================================================
# RELATÓRIO PDF EMPRESARIAL PROFISSIONAL (VERSÃO FINAL CORRIGIDA)
# =========================================================

@login_required
@check_group("Administrador")
def relatorio_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_confeitaria.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    elementos = []
    styles = getSampleStyleSheet()

    # =====================================================
    # LOCALIZAR LOGO (FORMA PROFISSIONAL E SEGURA)
    # =====================================================

    possible_paths = [

        os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png'),
        os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.png'),

    ]

    logo_path = None

    for path in possible_paths:
        if os.path.exists(path):
            logo_path = path
            break

    if logo_path:

        logo = Image(
            logo_path,
            width=4*cm,
            height=4*cm
        )

        logo.hAlign = 'LEFT'

        elementos.append(logo)

    else:

        elementos.append(
            Paragraph(
                "<font color='red'><b>Logo não encontrada</b></font>",
                styles["Normal"]
            )
        )

    elementos.append(Spacer(1, 0.5*cm))

    # =====================================================
    # TÍTULO
    # =====================================================

    titulo = Paragraph(
        "<b>RELATÓRIO GERENCIAL<br/>CONFEITARIA SILVIA</b>",
        styles["Heading1"]
    )

    elementos.append(titulo)

    elementos.append(Spacer(1, 0.3*cm))

    data_geracao = Paragraph(
        f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    )

    elementos.append(data_geracao)

    elementos.append(Spacer(1, 1*cm))

    # =====================================================
    # RESUMO GERAL
    # =====================================================

    total_produtos = Produto.objects.count()
    total_insumos = Insumo.objects.count()
    total_colaboradores = Colaborador.objects.count()

    elementos.append(
        Paragraph("<b>RESUMO GERAL</b>", styles["Heading2"])
    )

    elementos.append(Spacer(1, 0.3*cm))

    dados_resumo = [

        ["Indicador", "Quantidade"],
        ["Total de Produtos", str(total_produtos)],
        ["Total de Insumos", str(total_insumos)],
        ["Total de Colaboradores", str(total_colaboradores)],

    ]

    tabela_resumo = Table(
        dados_resumo,
        colWidths=[10*cm, 4*cm]
    )

    tabela_resumo.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

    ]))

    elementos.append(tabela_resumo)

    elementos.append(Spacer(1, 1*cm))

    # =====================================================
    # TABELA DE COLABORADORES
    # =====================================================

    elementos.append(
        Paragraph("<b>COLABORADORES CADASTRADOS</b>", styles["Heading2"])
    )

    elementos.append(Spacer(1, 0.3*cm))

    dados_colaboradores = [

        ["Nome", "Função"]

    ]

    colaboradores = Colaborador.objects.all().order_by("nome")

    for col in colaboradores:

        dados_colaboradores.append([

            col.nome,
            col.funcao if col.funcao else "Não informado"

        ])

    tabela_colaboradores = Table(

        dados_colaboradores,
        colWidths=[10*cm, 4*cm]

    )

    tabela_colaboradores.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#198754")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

    ]))

    elementos.append(tabela_colaboradores)

    elementos.append(Spacer(1, 1*cm))

    # =====================================================
    # RODAPÉ
    # =====================================================

    rodape = Paragraph(

        "Documento gerado automaticamente pelo Sistema de Gestão da Confeitaria Silvia.",

        styles["Italic"]

    )

    elementos.append(rodape)

    # =====================================================
    # GERAR PDF
    # =====================================================

    doc.build(elementos)

    return response
