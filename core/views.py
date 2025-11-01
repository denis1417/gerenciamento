from collections import defaultdict
from datetime import date, timedelta
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Avg, F, FloatField
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.conf import settings
from types import SimpleNamespace
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
    VistoriaInsumo
)
from .forms import (
    ProdutoProntoForm,
    FichaProducaoForm,
    InsumoForm,
    SaidaInsumoForm,
    ColaboradorForm
)

_FS_COLAB = None
_FS_INSUMOS = None
_FS_FICHAS = None
try:
    from confeitaria.repos_colaboradores import ColaboradoresRepo
    _FS_COLAB = ColaboradoresRepo()
except Exception:
    _FS_COLAB = None

try:
    from confeitaria.repos_insumos import InsumosRepo
    _FS_INSUMOS = InsumosRepo()
except Exception:
    _FS_INSUMOS = None

try:
    from confeitaria.repos_fichas import FichasRepo
    _FS_FICHAS = FichasRepo()
except Exception:
    _FS_FICHAS = None


def _wrap_dicts_as_objs(items):
    """
    Converte dicionários (vindos do Firestore) em objetos leves
    para que os templates possam acessar com notação ponto (item.campo).
    Adiciona métodos do modelo Django para compatibilidade com templates.
    """
    out = []
    for d in items:
        if isinstance(d, dict):
            obj = SimpleNamespace(**d)
            
            if 'quantidade_total' in d and 'unidade_base' in d:
                def formatar_quantidade_func():
                    q = float(d.get('quantidade_total', 0))
                    unidade = d.get('unidade_base', 'un')
                    if unidade == "g":
                        kg = int(q // 1000)
                        g = q % 1000
                        return f"{kg} kg {int(g)} g" if kg else f"{int(g)} g"
                    elif unidade == "ml":
                        l = int(q // 1000)
                        ml = q % 1000
                        return f"{l} L {int(ml)} ml" if l else f"{int(ml)} ml"
                    else:
                        return f"{int(q)} un"
                
                obj.formatar_quantidade = formatar_quantidade_func()
            
            out.append(obj)
        else:
            out.append(d)
    return out


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
            # redireciona pelo grupo
            if user.is_superuser or user.groups.filter(name="Administrador").exists():
                return redirect("home")
            elif user.groups.filter(name="RH").exists():
                return redirect("colaboradores_list")
            elif user.groups.filter(name="Insumos").exists():
                return redirect("insumos_list")
            elif user.groups.filter(name="Confeitaria").exists():
                return redirect("produtos_list")
            else:
                messages.error(request, "Usuário sem grupo definido.")
                return redirect("login")
        else:
            messages.error(request, "Usuário ou senha incorretos.")
            return redirect("login")
    users_exist = User.objects.exists()
    return render(request, "login.html", {"users_exist": users_exist})


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# HOME
# =========================================================

@login_required
def home(request):
    context = {
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
    """
    Lista de colaboradores - 100% FIRESTORE
    """
    query = request.GET.get('q')
    
    items = _FS_COLAB.list(limit=1000)
    if query:
        q = (query or "").strip().lower()
        items = [it for it in items if (it.get("nome") or "").lower().find(q) >= 0]
    colaboradores = _wrap_dicts_as_objs(items)
    return render(request, "core/colaboradores_list.html", {"colaboradores": colaboradores})


@login_required
@check_group("RH")
def colaboradores_create(request):
    use_fs = True  # 100% Firestore - FORÇADO para consistência
    form = ColaboradorForm(request.POST or None, request.FILES or None)
    
    if request.method == "POST":
        if form.is_valid():
            if use_fs:
                # Processa upload de imagem se existe
                foto_path = None
                if form.cleaned_data.get("foto"):
                    foto_file = form.cleaned_data["foto"]
                    # Salva o arquivo usando o modelo Django temporariamente para aproveitar o upload_to
                    temp_colaborador = Colaborador()
                    temp_colaborador.foto = foto_file
                    # Gera o caminho usando a lógica do Django
                    foto_path = f"colaboradores/{foto_file.name}"
                    full_path = os.path.join(settings.MEDIA_ROOT, foto_path)
                    
                    # Cria o diretório se não existe
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Salva o arquivo manualmente
                    with open(full_path, 'wb+') as destination:
                        for chunk in foto_file.chunks():
                            destination.write(chunk)
                
                data = {
                    "rc": form.cleaned_data.get("rc"),
                    "nome": form.cleaned_data.get("nome"),
                    "data_nascimento": form.cleaned_data.get("data_nascimento"),
                    "sexo": form.cleaned_data.get("sexo"),
                    "funcao": form.cleaned_data.get("funcao"),
                    "CPF_RG": form.cleaned_data.get("CPF_RG"),
                    "foto": foto_path,  # Salva apenas o caminho relativo
                    "email": form.cleaned_data.get("email"),
                    "celular": form.cleaned_data.get("celular"),
                    "cep": form.cleaned_data.get("cep"),
                    "logradouro": form.cleaned_data.get("logradouro"),
                    "numero": form.cleaned_data.get("numero"),
                    "bairro": form.cleaned_data.get("bairro"),
                    "cidade": form.cleaned_data.get("cidade"),
                    "estado": form.cleaned_data.get("estado"),
                    "complemento": form.cleaned_data.get("complemento"),
                }
                resultado = _FS_COLAB.create_colab(data)
                messages.success(
                    request, f"Colaborador {data['nome']} cadastrado com sucesso no Firestore!")
            else:
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
    use_fs = True  # 100% Firestore - FORÇADO para consistência
    
    if use_fs:
        colab_data = _FS_COLAB.get(str(id))
        if not colab_data:
            messages.error(request, "Colaborador não encontrado.")
            return redirect("colaboradores_list")
        
        # Converte data do Firestore para o formato do form se necessário
        initial_data = {}  # Começar com dict limpo em vez de copiar tudo
        
        # DEBUG: Vamos ver o que está vindo do Firestore
        print(f"DEBUG - Dados do Firestore: {colab_data}")
        print(f"DEBUG - data_nascimento: {colab_data.get('data_nascimento')}")
        print(f"DEBUG - tipo da data: {type(colab_data.get('data_nascimento'))}")
        
        # Mapear apenas os campos que o formulário precisa
        initial_data['rc'] = colab_data.get('rc', '')
        initial_data['nome'] = colab_data.get('nome', '')
        initial_data['sexo'] = colab_data.get('sexo', '')
        initial_data['funcao'] = colab_data.get('funcao', '')
        initial_data['CPF_RG'] = colab_data.get('CPF_RG', '')
        initial_data['email'] = colab_data.get('email', '')
        initial_data['celular'] = colab_data.get('celular', '')
        initial_data['cep'] = colab_data.get('cep', '')
        initial_data['logradouro'] = colab_data.get('logradouro', '')
        initial_data['numero'] = colab_data.get('numero', '')
        initial_data['bairro'] = colab_data.get('bairro', '')
        initial_data['cidade'] = colab_data.get('cidade', '')
        initial_data['estado'] = colab_data.get('estado', '')
        initial_data['complemento'] = colab_data.get('complemento', '')
        
        # Processamento específico da data de nascimento
        if colab_data.get("data_nascimento"):
            data_nascimento = colab_data["data_nascimento"]
            print(f"DEBUG - Processando data: {data_nascimento} (tipo: {type(data_nascimento)})")
            
            if hasattr(data_nascimento, "date"):
                # Se é um datetime, pega só a data
                converted_date = data_nascimento.date()
                initial_data["data_nascimento"] = converted_date
                print(f"DEBUG - Convertido datetime para date: {converted_date}")
            elif isinstance(data_nascimento, str):
                # Se é uma string, tenta converter para data
                try:
                    from datetime import datetime
                    converted_date = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
                    initial_data["data_nascimento"] = converted_date
                    print(f"DEBUG - Convertido string para date: {converted_date}")
                except (ValueError, TypeError):
                    # Se não conseguir converter, não adiciona a data
                    print(f"DEBUG - Erro ao converter string: {data_nascimento}")
            else:
                print(f"DEBUG - Tipo não reconhecido: {type(data_nascimento)}")
        else:
            print("DEBUG - Nenhuma data_nascimento encontrada nos dados")
        
        # Foto existente (não vai no initial_data)
        foto_existente = colab_data.get("foto", None)
        print(f"DEBUG - Foto existente: {foto_existente}")
            
        print(f"DEBUG - initial_data final para o form: {initial_data}")
            
        form = ColaboradorForm(request.POST or None, request.FILES or None, initial=initial_data)
        
        # Adicionar informação da foto existente para o template
        form.foto_existente = foto_existente
        
        if request.method == "POST" and form.is_valid():
            # Processa upload de nova imagem se existe
            foto_path = colab_data.get("foto")  # Mantém a foto existente por padrão
            if form.cleaned_data.get("foto"):
                foto_file = form.cleaned_data["foto"]
                # Gera o caminho usando a lógica do Django
                foto_path = f"colaboradores/{foto_file.name}"
                full_path = os.path.join(settings.MEDIA_ROOT, foto_path)
                
                # Cria o diretório se não existe
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Salva o arquivo manualmente
                with open(full_path, 'wb+') as destination:
                    for chunk in foto_file.chunks():
                        destination.write(chunk)
            
            data = {
                "rc": form.cleaned_data.get("rc"),
                "nome": form.cleaned_data.get("nome"),
                "data_nascimento": form.cleaned_data.get("data_nascimento"),
                "sexo": form.cleaned_data.get("sexo"),
                "funcao": form.cleaned_data.get("funcao"),
                "CPF_RG": form.cleaned_data.get("CPF_RG"),
                "foto": foto_path,  # Usa a foto nova ou mantém a existente
                "email": form.cleaned_data.get("email"),
                "celular": form.cleaned_data.get("celular"),
                "cep": form.cleaned_data.get("cep"),
                "logradouro": form.cleaned_data.get("logradouro"),
                "numero": form.cleaned_data.get("numero"),
                "bairro": form.cleaned_data.get("bairro"),
                "cidade": form.cleaned_data.get("cidade"),
                "estado": form.cleaned_data.get("estado"),
                "complemento": form.cleaned_data.get("complemento"),
            }
            _FS_COLAB.update_colab(str(id), data)
            messages.success(
                request, f"Colaborador {data['nome']} atualizado com sucesso!")
            return redirect("colaboradores_list")
    else:
        # SQLite
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
    use_fs = True  # 100% Firestore - FORÇADO para consistência
    
    if use_fs:
        # Firestore
        colab_data = _FS_COLAB.get(str(id))
        if not colab_data:
            messages.error(request, "Colaborador não encontrado.")
            return redirect("colaboradores_list")
        
        if request.method == "POST":
            _FS_COLAB.delete(str(id))
            messages.success(
                request, f"Colaborador {colab_data.get('nome', 'N/A')} deletado com sucesso!")
            return redirect("colaboradores_list")
        
        # Cria objeto para o template
        colaborador = SimpleNamespace(**colab_data)
    else:
        # SQLite
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
    use_fs = True  # 100% Firestore - FORÇADO para consistência
    
    if use_fs:
        # Firestore
        colab_data = _FS_COLAB.get(str(id))
        if not colab_data:
            messages.error(request, "Colaborador não encontrado.")
            return redirect("colaboradores_list")
        colaborador = SimpleNamespace(**colab_data)
    else:
        # SQLite
        colaborador = get_object_or_404(Colaborador, id=id)
    
    return render(request, "core/colaboradores_detail.html", {"colaborador": colaborador})


# =========================================================
# USUÁRIOS
# =========================================================

@login_required
@check_group("Administrador")
def usuarios_create(request):
    """
    Cria usuários Django vinculados a colaboradores do Firestore
    """
    # Busca colaboradores do Firestore
    colaboradores_list = _FS_COLAB.list(limit=1000)
    colaboradores = _wrap_dicts_as_objs(colaboradores_list)
    
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
            # Busca colaborador no Firestore
            colab_data = _FS_COLAB.get(str(colaborador_id))
            if not colab_data:
                messages.error(request, "Colaborador não encontrado.")
                return redirect("criar_usuario")
            
            # Cria usuário Django
            user = User.objects.create_user(username=username, password=senha_nova)
            if grupo:
                grupo_obj, _ = Group.objects.get_or_create(name=grupo)
                user.groups.add(grupo_obj)
            
            # Atualiza colaborador no Firestore com o ID do usuário
            _FS_COLAB.update_colab(str(colaborador_id), {
                **colab_data,
                'usuario_id': user.id,
                'usuario_username': user.username
            })
            
            messages.success(request, f"Usuário {username} cadastrado com sucesso!")
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
    """Lista de insumos - 100% FIRESTORE"""
    items = _FS_INSUMOS.list(limit=1000)
    insumos = _wrap_dicts_as_objs(items)
    return render(request, "core/insumos_list.html", {"insumos": insumos})


@login_required
@check_group("Insumos")
def insumos_create(request):
    use_fs = True  # 100% Firestore - FORÇADO
    form = InsumoForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        if use_fs:
            # Salva no Firestore
            data = {
                "nome": form.cleaned_data.get("nome"),
                "descricao": form.cleaned_data.get("descricao"),
                "unidade_base": form.cleaned_data.get("unidade_base"),
                "unidade_complementar": form.cleaned_data.get("unidade_complementar"),
                "fator_conversao": form.cleaned_data.get("fator_conversao"),
                "quantidade_total": form.cleaned_data.get("quantidade_total"),
                "preco_unitario": form.cleaned_data.get("preco_unitario"),
            }
            _FS_INSUMOS.create(data)
            messages.success(request, "Insumo cadastrado com sucesso no Firestore!")
        else:
            # Salva no SQLite
            form.save()
            messages.success(request, "Insumo cadastrado com sucesso!")
        return redirect("insumos_list")
    
    return render(request, "core/form.html", {"form": form, "titulo": "Cadastrar Insumo"})


@login_required
@check_group("Insumos")
def insumos_edit(request, id):
    use_fs = True  # 100% Firestore - FORÇADO
    
    if use_fs:
        # Busca no Firestore
        insumo_data = _FS_INSUMOS.get(str(id))
        if not insumo_data:
            messages.error(request, "Insumo não encontrado.")
            return redirect("insumos_list")
        
        # Mapear dados do Firestore para o formulário
        quantidade_total = insumo_data.get('quantidade_total', 0)
        unidade_base = insumo_data.get('unidade_base', 'g')
        
        # Quebrar quantidade_total em principal e complementar
        if unidade_base in ['g', 'ml']:
            principal = int(quantidade_total // 1000)  # kg ou L
            complementar = int(quantidade_total % 1000)     # g ou ml (como inteiro)
        else:
            principal = int(quantidade_total)
            complementar = 0
            
        form_initial = {
            'nome': insumo_data.get('nome'),
            'unidade_base': unidade_base,
            'quantidade_principal': principal,
            'quantidade_complementar': complementar,
        }
        form = InsumoForm(request.POST or None, initial=form_initial)
        
        if request.method == "POST" and form.is_valid():
            # Converter principal + complementar de volta para quantidade_total
            principal = form.cleaned_data.get("quantidade_principal", 0)
            complementar = form.cleaned_data.get("quantidade_complementar", 0)
            unidade = form.cleaned_data.get("unidade_base")
            
            if unidade in ['g', 'ml']:
                quantidade_total = (principal * 1000) + complementar  # kg→g ou L→ml
            else:
                quantidade_total = principal
                
            data = {
                "nome": form.cleaned_data.get("nome"),
                "unidade_base": unidade,
                "quantidade_total": quantidade_total,
                "descricao": insumo_data.get("descricao"),  # Preservar campos não editáveis
                "unidade_complementar": insumo_data.get("unidade_complementar"),
                "fator_conversao": insumo_data.get("fator_conversao"),
                "preco_unitario": insumo_data.get("preco_unitario"),
                "criado_em": insumo_data.get("criado_em"),  # Preservar timestamp
                "atualizado_em": insumo_data.get("atualizado_em"),
            }
            _FS_INSUMOS.set(str(id), data)
            messages.success(request, "Insumo atualizado com sucesso!")
            return redirect("insumos_list")
    else:
        # SQLite
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
    use_fs = True  # 100% Firestore - FORÇADO
    
    if use_fs:
        # Firestore
        insumo_data = _FS_INSUMOS.get(str(id))
        if not insumo_data:
            messages.error(request, "Insumo não encontrado.")
            return redirect("insumos_list")
        
        if request.method == "POST":
            _FS_INSUMOS.delete(str(id))
            messages.success(request, f"Insumo {insumo_data.get('nome', 'N/A')} deletado com sucesso!")
            return redirect("insumos_list")
        
        # Cria objeto formatado para o template
        insumo = _wrap_dicts_as_objs([insumo_data])[0]
    else:
        # SQLite
        insumo = get_object_or_404(Insumo, id=id)
        if request.method == "POST":
            insumo.delete()
            messages.success(request, f"Insumo {insumo.nome} deletado com sucesso!")
            return redirect("insumos_list")
    
    return render(request, "core/delete.html", {"obj": insumo})


# =========================================================
# SAÍDA DE INSUMOS
# =========================================================

@login_required
@check_group("Insumos")
def saida_insumo_list(request):
    """
    Lista de saídas de insumos - 100% FIRESTORE
    """
    from confeitaria.repos_saidas import SaidasRepo
    from datetime import datetime, date
    
    saidas_repo = SaidasRepo()
    saidas_list = saidas_repo.list(limit=1000)
    
    # Converte para objetos acessíveis pelo template
    saidas = []
    for s in saidas_list:
        saida_obj = SimpleNamespace(**s)
        
        # Cria objetos simulados para insumo e colaboradores
        saida_obj.insumo = SimpleNamespace(
            id=s.get('insumo_id'),
            nome=s.get('insumo_nome', ''),
            unidade_base=s.get('insumo_unidade', '')
        )
        
        # Colaborador entregando
        saida_obj.colaborador_entregando = SimpleNamespace(
            id=s.get('colaborador_entregando_id'),
            nome=s.get('colaborador_entregando_nome', '')
        )
        
        # Colaborador que retira
        saida_obj.colaborador_retira = SimpleNamespace(
            id=s.get('colaborador_retira_id'),
            nome=s.get('colaborador_retira_nome', '')
        )
        
        # Converte data ISO para objeto date/datetime
        data_value = s.get('data')
        
        if isinstance(data_value, str):
            try:
                # Tenta parsear como datetime ISO (com hora)
                dt = datetime.fromisoformat(data_value.replace('Z', '+00:00'))
                saida_obj.data = dt  # Mantém como datetime
            except Exception:
                try:
                    # Tenta parsear como data simples
                    saida_obj.data = datetime.strptime(data_value[:10], "%Y-%m-%d").date()
                except Exception:
                    saida_obj.data = datetime.now()
        elif hasattr(data_value, 'date'):
            # Se já é um datetime, usa direto
            saida_obj.data = data_value
        elif isinstance(data_value, date):
            # Se é uma data, converte para datetime
            saida_obj.data = datetime.combine(data_value, datetime.min.time())
        else:
            saida_obj.data = datetime.now()
        
        # Calcula quantidade_total para o template
        saida_obj.quantidade_total = float(s.get('quantidade_principal', 0)) + float(s.get('quantidade_complementar', 0))
        
        # Unidade
        saida_obj.unidade = s.get('unidade', 'un')
        
        saidas.append(saida_obj)
    
    return render(request, "core/saida_insumo_list.html", {"saidas": saidas})


@login_required
@check_group("Insumos")
def saida_insumo_create(request):
    """
    Registra saída de insumo - 100% FIRESTORE
    """
    use_fs = True  # 100% Firestore
    
    if request.method == "POST":
        from confeitaria.repos_saidas import SaidasRepo
        saidas_repo = SaidasRepo()
        
        # Pega dados diretamente do POST (não usa form.cleaned_data para evitar validação do ModelForm)
        insumo_id = request.POST.get('insumo')
        colab_entregando_id = request.POST.get('colaborador_entregando')
        colab_retira_id = request.POST.get('colaborador_retira')
        quantidade_str = request.POST.get('quantidade', '0')
        unidade = request.POST.get('unidade')
        
        # Valida quantidade
        try:
            quantidade = float(quantidade_str)
        except (ValueError, TypeError):
            quantidade = 0
        
        if quantidade == 0:
            messages.error(request, "Você precisa informar a quantidade.")
            # Recarrega o formulário
            form = SaidaInsumoForm(request.POST, use_firestore=use_fs)
            return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})
        
        # Busca dados do Firestore
        insumo_data = _FS_INSUMOS.get(str(insumo_id))
        colab_entregando_data = _FS_COLAB.get(str(colab_entregando_id))
        colab_retira_data = _FS_COLAB.get(str(colab_retira_id))
        
        if not insumo_data:
            messages.error(request, "Insumo não encontrado no Firestore.")
            form = SaidaInsumoForm(request.POST, use_firestore=use_fs)
            return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})
        
        if not colab_entregando_data:
            messages.error(request, "Colaborador que entrega não encontrado no Firestore.")
            form = SaidaInsumoForm(request.POST, use_firestore=use_fs)
            return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})
        
        if not colab_retira_data:
            messages.error(request, "Colaborador que retira não encontrado no Firestore.")
            form = SaidaInsumoForm(request.POST, use_firestore=use_fs)
            return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})
        
        # Valida estoque
        quantidade_total = float(insumo_data.get('quantidade_total', 0))
        if quantidade > quantidade_total:
            messages.error(
                request,
                f"A quantidade solicitada ({quantidade} {insumo_data.get('unidade_base', '')}) "
                f"excede o estoque disponível ({quantidade_total} {insumo_data.get('unidade_base', '')})."
            )
            form = SaidaInsumoForm(request.POST, use_firestore=use_fs)
            return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})
        
        # Atualiza estoque no Firestore
        nova_quantidade = quantidade_total - quantidade
        _FS_INSUMOS.set(str(insumo_id), {
            **insumo_data,  # Mantém todos os campos existentes
            'quantidade_total': nova_quantidade
        })
        
        # Salva a saída no Firestore
        saida_data = {
            'insumo_id': str(insumo_id),
            'insumo_nome': insumo_data.get('nome', ''),
            'insumo_unidade': insumo_data.get('unidade_base', ''),
            'colaborador_entregando_id': str(colab_entregando_id),
            'colaborador_entregando_nome': colab_entregando_data.get('nome', ''),
            'colaborador_retira_id': str(colab_retira_id),
            'colaborador_retira_nome': colab_retira_data.get('nome', ''),
            'quantidade_principal': float(quantidade),
            'quantidade_complementar': 0.0,
            'unidade': unidade,
            'data': timezone.now().isoformat(),
            'observacoes': '',
        }
        
        saidas_repo.create_saida(saida_data)
        
        messages.success(request, "Saída de insumo registrada com sucesso no Firestore!")
        return redirect("saida_insumo_list")
    
    # GET request - apenas exibe o formulário
    form = SaidaInsumoForm(use_firestore=use_fs)
    return render(request, "core/form.html", {"form": form, "titulo": "Registrar Saída de Insumo"})


@login_required
@check_group("Insumos")
def saida_insumo_delete(request, id):
    """
    Deleta uma saída de insumo e devolve a quantidade retirada ao insumo original.
    100% FIRESTORE
    """
    from confeitaria.repos_saidas import SaidasRepo
    saidas_repo = SaidasRepo()
    
    saida_data = saidas_repo.get(str(id))
    
    if not saida_data:
        messages.error(request, "Saída de insumo não encontrada.")
        return redirect('saida_insumo_list')
    
    if request.method == "POST":
        # Recupera a quantidade total em unidade base
        quantidade_devolvida = float(saida_data.get('quantidade_principal', 0)) + float(saida_data.get('quantidade_complementar', 0))
        
        # Busca o insumo no Firestore e devolve a quantidade
        insumo_id = saida_data.get('insumo_id')
        insumo_data = _FS_INSUMOS.get(str(insumo_id))
        
        if insumo_data:
            quantidade_atual = float(insumo_data.get('quantidade_total', 0))
            nova_quantidade = quantidade_atual + quantidade_devolvida
            _FS_INSUMOS.set(str(insumo_id), {**insumo_data, 'quantidade_total': nova_quantidade})
        
        # Deleta a saída do Firestore
        saidas_repo.delete(str(id))
        
        messages.success(
            request, f"Saída de {saida_data.get('insumo_nome', 'insumo')} removida com sucesso e estoque atualizado.")
        return redirect('saida_insumo_list')
    
    # Cria objeto para o template
    saida = SimpleNamespace(**saida_data)
    saida.insumo = SimpleNamespace(nome=saida_data.get('insumo_nome', ''))
    saida.quantidade_total = float(saida_data.get('quantidade_principal', 0)) + float(saida_data.get('quantidade_complementar', 0))
    saida.unidade = saida_data.get('unidade', 'un')
    
    # Formata a exibição da quantidade (ex: "12030 kg")
    quantidade_formatada = f"{saida.quantidade_total:.0f}" if saida.quantidade_total == int(saida.quantidade_total) else f"{saida.quantidade_total}"
    saida.exibir_quantidade = f"{quantidade_formatada} {saida.unidade}"
    
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
    Busca produtos e fichas do Firestore.
    """
    from confeitaria.repos_produtos import ProdutosRepo
    from confeitaria.repos_fichas import FichasRepo
    
    produtos_repo = ProdutosRepo()
    fichas_repo = FichasRepo()
    
    items = produtos_repo.list(limit=1000)
    produtos = []
    
    for d in items:
        class ProdutoProntoFS:
            pass
        p = ProdutoProntoFS()
        p.id = d.get('id', '')
        p.catalogo_nome = d.get('catalogo_nome', '')
        p.quantidade = d.get('quantidade', 0)
        
        # Formatação igual ao SQLite (ex: 1,0)
        try:
            p.quantidade_formatada = f"{float(p.quantidade):.1f}".replace('.', ',')
        except Exception:
            p.quantidade_formatada = str(p.quantidade)
        
        # Datas
        from datetime import date, timedelta, datetime
        def parse_data(dt):
            from datetime import date, datetime
            # Google Firestore DatetimeWithNanoseconds
            if hasattr(dt, 'date'):
                return dt.date()
            if isinstance(dt, date):
                return dt
            if isinstance(dt, datetime):
                return dt.date()
            if isinstance(dt, str):
                try:
                    return datetime.strptime(dt[:10], "%Y-%m-%d").date()
                except Exception:
                    return None
            return None
        
        p.data_fabricacao = parse_data(d.get('data_fabricacao'))
        p.data_validade = parse_data(d.get('data_validade'))
        p.peso_produto = d.get('peso_produto', 0)
        
        # Verificar se existe ficha para este produto no Firestore
        try:
            fichas_do_produto = fichas_repo.list_by_produto(str(p.id), limit=1)
            p.ficha_existe = len(fichas_do_produto) > 0
            p.ficha = SimpleNamespace(**fichas_do_produto[0]) if p.ficha_existe else None
        except Exception as e:
            p.ficha_existe = False
            p.ficha = None
        
        # Classe CSS conforme validade
        p.row_class = ""
        if p.data_validade:
            if p.data_validade < date.today():
                p.row_class = "produto-vencido"
            elif p.data_validade == date.today():
                p.row_class = "produto-hoje"
            elif p.data_validade <= date.today() + timedelta(days=3):
                p.row_class = "produto-proximo"
        
        produtos.append(p)
    
    return render(request, "core/produtos_list.html", {"produtos": produtos})


# -------------------- CADASTRAR PRODUTO --------------------
@login_required
@check_group("Confeitaria")
def produtos_create(request):
    """
    Permite o cadastro de novos produtos prontos.
    Salva APENAS no Firestore.
    Acesso: grupo Confeitaria e Administrador.
    """
    form = ProdutoProntoForm(request.POST or None, use_firestore=True)
    if request.method == "POST" and form.is_valid():
        from confeitaria.repos_produtos import ProdutosRepo
        from confeitaria.repos_catalogo import CatalogoRepo
        
        repo = ProdutosRepo()
        catalogo_repo = CatalogoRepo()
        cleaned = form.cleaned_data
        
        # Busca dados do catálogo no Firestore
        catalogo_id = cleaned.get('catalogo')
        catalogo_nome = ''
        if catalogo_id:
            cat_data = catalogo_repo.get(str(catalogo_id))
            if cat_data:
                catalogo_nome = cat_data.get('nome', '')
        
        data = {
            'quantidade': cleaned.get('quantidade', 0),
            'data_fabricacao': cleaned.get('data_fabricacao').isoformat() if cleaned.get('data_fabricacao') else None,
            'data_validade': cleaned.get('data_validade').isoformat() if cleaned.get('data_validade') else None,
            'peso_produto': cleaned.get('peso_produto', 0),
            'catalogo_id': str(catalogo_id) if catalogo_id else None,
            'catalogo_nome': catalogo_nome,
        }
        
        # Salva no Firestore
        result = repo.create_produto(data)
        
        messages.success(request, f"Produto {data['catalogo_nome']} cadastrado com sucesso!")
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
    from confeitaria.repos_produtos import ProdutosRepo
    repo = ProdutosRepo()
    produto_data = repo.get(str(id))
    if not produto_data:
        from django.http import Http404
        raise Http404("Produto não encontrado no Firestore.")

    # Preenche o formulário manualmente
    from core.forms import ProdutoProntoForm
    from datetime import datetime, date
    def parse_data(dt):
        if hasattr(dt, 'date'):
            return dt.date()
        if isinstance(dt, date):
            return dt
        if isinstance(dt, datetime):
            return dt.date()
        if isinstance(dt, str):
            try:
                return datetime.strptime(dt[:10], "%Y-%m-%d").date()
            except Exception:
                return None
        return None

    initial = {
        'quantidade': produto_data.get('quantidade', 0),
        'data_fabricacao': parse_data(produto_data.get('data_fabricacao')),
        'data_validade': parse_data(produto_data.get('data_validade')),
        'peso_produto': produto_data.get('peso_produto', 0),
    }
    
    # Catalogo: busca pelo id salvo no Firestore
    from confeitaria.repos_catalogo import CatalogoRepo
    catalogo_repo = CatalogoRepo()
    catalogo_id = produto_data.get('catalogo_id')
    if catalogo_id:
        catalogo_data = catalogo_repo.get(str(catalogo_id))
        if catalogo_data:
            # Cria objeto simulado para o formulário
            initial['catalogo'] = catalogo_id  # Passa o ID do Firestore
        else:
            initial['catalogo'] = None
    else:
        initial['catalogo'] = None

    form = ProdutoProntoForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        # Atualiza no Firestore
        cleaned = form.cleaned_data
        
        # Busca nome do catálogo no Firestore
        catalogo_escolhido = cleaned.get('catalogo')
        catalogo_nome = ''
        if catalogo_escolhido:
            cat_data = catalogo_repo.get(str(catalogo_escolhido))
            if cat_data:
                catalogo_nome = cat_data.get('nome', '')
        
        update_data = {
            'quantidade': cleaned.get('quantidade', 0),
            'data_fabricacao': cleaned.get('data_fabricacao').isoformat() if cleaned.get('data_fabricacao') else None,
            'data_validade': cleaned.get('data_validade').isoformat() if cleaned.get('data_validade') else None,
            'peso_produto': cleaned.get('peso_produto', 0),
            'catalogo_id': str(catalogo_escolhido) if catalogo_escolhido else None,
            'catalogo_nome': catalogo_nome,
        }
        repo.update_produto(str(id), update_data)
        messages.success(
            request, f"Produto {update_data['catalogo_nome']} atualizado com sucesso!")
        return redirect("produtos_list")

    titulo = f"Editar Produto: {produto_data.get('catalogo_nome', '')}" if produto_data.get('catalogo_nome') else "Editar Produto"
    return render(request, "core/form.html", {"form": form, "titulo": titulo})


# -------------------- EXCLUIR PRODUTO --------------------
@login_required
@check_group("Confeitaria")
def produtos_delete(request, id):
    """
    Exclui um produto existente.
    Acesso: grupo Confeitaria e Administrador.
    """
    from confeitaria.repos_produtos import ProdutosRepo
    repo = ProdutosRepo()
    produto_data = repo.get(str(id))
    if not produto_data:
        from django.http import Http404
        raise Http404("Produto não encontrado no Firestore.")

    class ProdutoProntoFS:
        pass
    p = ProdutoProntoFS()
    p.id = produto_data.get('id', '')
    p.catalogo_nome = produto_data.get('catalogo_nome', '')
    p.quantidade = produto_data.get('quantidade', 0)
    try:
        p.quantidade_formatada = f"{float(p.quantidade):.1f}".replace('.', ',')
    except Exception:
        p.quantidade_formatada = str(p.quantidade)

    if request.method == "POST":
        repo.delete(str(id))
        messages.success(
            request, f"Produto {p.catalogo_nome} excluído com sucesso!")
        return redirect("produtos_list")

    # Monta string igual ao modelo desejado
    obj_str = f"{p.catalogo_nome} - {p.quantidade_formatada} unidades"
    return render(request, "core/confirm_delete.html", {"obj": obj_str})


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
    from confeitaria.repos_insumos import InsumosRepo
    from confeitaria.repos_saidas import SaidasRepo
    from confeitaria.repos_fichas import FichasRepo
    insumos_repo = InsumosRepo()
    saidas_repo = SaidasRepo()
    fichas_repo = FichasRepo()

    insumos = insumos_repo.list(limit=1000)
    saidas = saidas_repo.list(limit=1000)
    fichas = fichas_repo.list(limit=1000)

    for insumo in insumos:
        insumo_id = insumo.get('id')
        # Quantidade retirada (somatório das saídas)
        soma_principal = sum(float(s.get('quantidade_principal', 0)) for s in saidas if s.get('insumo_id') == insumo_id)
        soma_complementar = sum(float(s.get('quantidade_complementar', 0)) for s in saidas if s.get('insumo_id') == insumo_id)
        retirado = soma_principal + soma_complementar

        # Quantidade usada em fichas (somatório das fichas que usam esse insumo)
        usado = sum(float(f.get('quantidade_usada', 0)) for f in fichas if f.get('insumo_id') == insumo_id)

        teorico = max(retirado - usado, 0)

        # Simula objeto insumo para template
        class InsumoFS:
            pass
        insumo_obj = InsumoFS()
        insumo_obj.id = insumo_id
        insumo_obj.nome = insumo.get('nome', '')
        insumo_obj.unidade_base = insumo.get('unidade_base', '')
        insumo_obj.quantidade_total = insumo.get('quantidade_total', 0)

        relatorio.append({
            'insumo': insumo_obj,
            'retirado': retirado,
            'usado': usado,
            'teorico': teorico,
        })

    # Salvar checklist / vistoria - 100% FIRESTORE
    if request.method == "POST":
        from confeitaria.repos_vistorias import VistoriasRepo
        vistorias_repo = VistoriasRepo()
        
        for item in relatorio:
            real_str = request.POST.get(f"real_{item['insumo'].id}", "")
            if not real_str:
                continue
            try:
                real = float(real_str)
            except ValueError:
                continue  # Ignora valores inválidos
            desperdicio = item['teorico'] - real

            # Salva no Firestore
            vistoria_data = {
                'insumo_id': item['insumo'].id,
                'insumo_nome': item['insumo'].nome,
                'insumo_unidade': item['insumo'].unidade_base,
                'quantidade_retirada': float(item['retirado']),
                'quantidade_usada': float(item['usado']),
                'quantidade_teorica': float(item['teorico']),
                'quantidade_real': float(real),
                'desperdicio': float(desperdicio),
                'data_vistoria': date.today().isoformat(),
            }
            vistorias_repo.create(vistoria_data)

        messages.success(request, "✅ Vistoria registrada com sucesso!")
        return redirect('relatorio_insumos')

    # Histórico de checklists agrupados por data - 100% FIRESTORE
    from confeitaria.repos_vistorias import VistoriasRepo
    from datetime import datetime
    vistorias_repo = VistoriasRepo()
    datas_vistoria = vistorias_repo.get_datas_vistoria()
    
    # Formata datas para o formato brasileiro
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    checklists = []
    for data_str in datas_vistoria:
        try:
            # Converte string ISO para datetime
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            # Formata: "17 de Outubro de 2025"
            data_formatada = f"{data_obj.day} de {meses[data_obj.month]} de {data_obj.year}"
            checklists.append({
                'data_vistoria': data_str,  # Mantém formato ISO para links
                'data_formatada': data_formatada  # Formato brasileiro para exibição
            })
        except Exception:
            # Se falhar, mantém formato original
            checklists.append({
                'data_vistoria': data_str,
                'data_formatada': data_str
            })

    context = {
        'relatorio': relatorio,
        'checklists': checklists,
    }

    return render(request, 'core/relatorio_insumos.html', context)


@login_required
def visualizar_checklist(request, data_vistoria):
    """
    Visualiza checklist de uma vistoria específica com opção de impressão.
    100% FIRESTORE
    """
    from confeitaria.repos_vistorias import VistoriasRepo
    vistorias_repo = VistoriasRepo()
    
    # Busca vistorias do Firestore
    vistorias_dict = vistorias_repo.get_by_data(data_vistoria)
    
    # Converte para lista de objetos
    itens = []
    for vistoria_id, vistoria_data in vistorias_dict.items():
        item = SimpleNamespace(**vistoria_data)
        item.id = vistoria_id
        
        # Cria objeto insumo simplificado para o template
        item.insumo = SimpleNamespace(
            nome=vistoria_data.get('insumo_nome', ''),
            unidade_base=vistoria_data.get('insumo_unidade', '')
        )
        itens.append(item)
    
    return render(request, 'core/checklist_vistoria.html', {
        'itens': itens,
        'data_vistoria': data_vistoria
    })


@login_required
@check_group(["Administrador", "Confeitaria"])
def excluir_checklist(request, data_vistoria):
    """
    Exclui checklist de uma data específica.
    100% FIRESTORE
    """
    if request.method == "POST":
        from confeitaria.repos_vistorias import VistoriasRepo
        vistorias_repo = VistoriasRepo()
        
        deleted_count = vistorias_repo.delete_by_data(data_vistoria)
        messages.success(request, f"Checklist excluído com sucesso! ({deleted_count} registro(s) removido(s))")
        return redirect('relatorio_insumos')
    return redirect('relatorio_insumos')


@login_required
@check_group(["Administrador", "Confeitaria"])
def criar_ficha(request):
    """
    Cria uma ficha de produção usando APENAS Firestore (sem SQLite).
    100% FIRESTORE
    """
    print(f"[DEBUG] Iniciando criar_ficha - Método: {request.method}")
    
    # Busca produtos e saídas do Firestore
    from confeitaria.repos_produtos import ProdutosRepo
    from confeitaria.repos_fichas import FichasRepo
    from confeitaria.repos_saidas import SaidasRepo
    from datetime import datetime
    
    produtos_repo = ProdutosRepo()
    fichas_repo = FichasRepo()
    saidas_repo = SaidasRepo()
    
    produtos_list_dict = produtos_repo.list(limit=1000)
    
    # Converte produtos Firestore para objetos com atributos acessíveis
    produtos_list = []
    for p_dict in produtos_list_dict:
        p_obj = SimpleNamespace(**p_dict)
        # Garantir que catalogo seja um objeto com atributo nome
        if hasattr(p_obj, 'catalogo_nome'):
            p_obj.catalogo = SimpleNamespace(nome=p_obj.catalogo_nome)
        produtos_list.append(p_obj)
    
    # Busca colaborador logado do Firestore
    colaborador_logado = None
    if not request.user.is_superuser:
        # Busca colaborador pelo usuario_id no Firestore
        colaboradores_list = _FS_COLAB.list(limit=1000)
        for colab_data in colaboradores_list:
            if colab_data.get('usuario_id') == request.user.id:
                colaborador_logado = SimpleNamespace(**colab_data)
                break

    # Produto selecionado via GET ou POST
    produto_id = request.GET.get("produto") or request.POST.get("produto")
    print(f"[DEBUG] produto_id obtido: {produto_id}")
    
    produto = None
    if produto_id:
        produto_dict = produtos_repo.get(produto_id)
        if produto_dict:
            produto = SimpleNamespace(**produto_dict)
            if hasattr(produto, 'catalogo_nome'):
                produto.catalogo = SimpleNamespace(nome=produto.catalogo_nome)
            produto.id = produto_id
            print(f"[DEBUG] Produto carregado do Firestore: ID={produto_id}")

    # Insumos disponíveis do Firestore - apenas saídas com quantidade > 0
    saidas_list = saidas_repo.list(limit=1000)
    insumos_disponiveis = []
    for s in saidas_list:
        quantidade_total = float(s.get('quantidade_principal', 0)) + float(s.get('quantidade_complementar', 0))
        if quantidade_total > 0:
            # Cria objeto simulado para compatibilidade com template
            saida_obj = SimpleNamespace(**s)
            saida_obj.quantidade_total = quantidade_total
            saida_obj.insumo = SimpleNamespace(
                id=s.get('insumo_id'),
                nome=s.get('insumo_nome', ''),
                unidade_base=s.get('insumo_unidade', '')
            )
            insumos_disponiveis.append(saida_obj)
    
    print(f"[DEBUG] Insumos disponíveis (com saídas): {len(insumos_disponiveis)}")

    # Inicializa formulário com peso do produto, se existir
    initial_data = {"peso_produto": getattr(produto, 'peso_produto', 0)} if produto else {}
    form = FichaProducaoForm(request.POST or None, initial=initial_data)
    print(f"[DEBUG] Formulário inicializado")

    if request.method == "POST":
        print(f"[DEBUG] POST recebido")
        
        # Verifica senha
        senha = request.POST.get("senha_confirmacao")
        user = authenticate(username=request.user.username, password=senha)
        if user is None:
            print(f"[DEBUG] Senha incorreta")
            messages.error(request, "Senha incorreta. Tente novamente.")
            return redirect(request.path)

        if not produto:
            print(f"[DEBUG] Produto não selecionado")
            messages.error(request, "Selecione um produto.")
            return redirect(request.path)

        print(f"[DEBUG] Validando formulário...")
        if form.is_valid():
            print(f"[DEBUG] Formulário válido, salvando no Firestore...")
            print(f"[DEBUG] produto_id a ser salvo na ficha: '{produto_id}' (tipo: {type(produto_id)})")
            
            # Prepara dados da ficha para o Firestore com TODOS os campos do formulário
            ficha_data = {
                'produto_id': str(produto_id),  # Garantir que seja string
                'produto_nome': getattr(produto.catalogo, 'nome', '') if hasattr(produto, 'catalogo') else '',
                'peso_produto': float(form.cleaned_data.get('peso_produto', 0)),
                'data_fabricacao': form.cleaned_data.get('data_fabricacao').isoformat() if form.cleaned_data.get('data_fabricacao') else None,
                'data_validade': None,  # Não vem do formulário de ficha, é do produto
                'categoria': form.cleaned_data.get('categoria', ''),
                'textura': form.cleaned_data.get('textura', ''),
                'validade': int(form.cleaned_data.get('validade', 0)) if form.cleaned_data.get('validade') else None,
                'armazenamento': form.cleaned_data.get('armazenamento', ''),
                'calorias': int(form.cleaned_data.get('calorias', 0)) if form.cleaned_data.get('calorias') else None,
                'tempo_preparo': int(form.cleaned_data.get('tempo_preparo', 0)) if form.cleaned_data.get('tempo_preparo') else None,
                'perda_aceitavel': form.cleaned_data.get('perda_aceitavel', ''),
                'rendimento': form.cleaned_data.get('rendimento', ''),
                'observacoes': form.cleaned_data.get('observacoes', ''),
                'assinado_por': colaborador_logado.nome if colaborador_logado else request.user.username,
                'colaborador_id': colaborador_logado.id if colaborador_logado else None,
                'colaborador_nome': colaborador_logado.nome if colaborador_logado else None,
                'data_assinatura': datetime.now(),
                'insumos': []
            }
            
            # Processar insumos usados
            saida_ids = request.POST.getlist("insumo_id[]")
            quantidades = request.POST.getlist("quantidade_usada[]")
            unidades = request.POST.getlist("unidade[]")

            insumos_registrados = 0
            for i, saida_id in enumerate(saida_ids):
                quantidade_str = quantidades[i] if i < len(quantidades) else ""
                if saida_id and quantidade_str and float(quantidade_str) > 0:
                    try:
                        # Busca a saída no Firestore
                        saida_data = saidas_repo.get(str(saida_id))
                        if not saida_data:
                            print(f"[DEBUG] Saída {saida_id} não encontrada")
                            continue
                        
                        quantidade_usada = float(quantidades[i])
                        unidade = unidades[i]

                        # Adiciona insumo à lista da ficha
                        ficha_data['insumos'].append({
                            'insumo_id': saida_data.get('insumo_id'),
                            'insumo_nome': saida_data.get('insumo_nome'),
                            'quantidade_usada': quantidade_usada,
                            'unidade': unidade,
                            'data_registro': datetime.now()
                        })

                        # Atualiza estoque da saída no Firestore
                        quantidade_principal = float(saida_data.get('quantidade_principal', 0))
                        quantidade_complementar = float(saida_data.get('quantidade_complementar', 0))
                        total_disponivel = quantidade_principal + quantidade_complementar
                        restante = total_disponivel - quantidade_usada

                        if restante >= 0:
                            if quantidade_usada <= quantidade_principal:
                                nova_principal = quantidade_principal - quantidade_usada
                                nova_complementar = quantidade_complementar
                            else:
                                nova_principal = 0
                                nova_complementar = max(restante, 0)
                        else:
                            nova_principal = 0
                            nova_complementar = 0

                        # Atualiza a saída no Firestore
                        saidas_repo.update(str(saida_id), {
                            'quantidade_principal': nova_principal,
                            'quantidade_complementar': nova_complementar
                        })
                        
                        insumos_registrados += 1
                        
                    except Exception as e:
                        print(f"[DEBUG] Erro ao processar saída {saida_id}: {e}")
                        continue

            # Salva a ficha no Firestore
            try:
                ficha_criada = fichas_repo.create_ficha(ficha_data)
                ficha_id = ficha_criada.get('id')
                print(f"[DEBUG] Ficha criada no Firestore com ID: {ficha_id}")
                
                if insumos_registrados == 0:
                    messages.warning(request, "Ficha criada, mas nenhum insumo foi registrado.")
                else:
                    messages.success(request, f"Ficha criada e assinada com sucesso! {insumos_registrados} insumo(s) registrado(s).")
                
                print(f"[DEBUG] Redirecionando para visualizar_ficha com ficha_id={ficha_id}")
                return redirect("visualizar_ficha", ficha_id=ficha_id)
                
            except Exception as e:
                print(f"[DEBUG] Erro ao salvar ficha no Firestore: {e}")
                messages.error(request, f"Erro ao criar ficha: {str(e)}")
                return redirect(request.path)
        else:
            print(f"[DEBUG] Formulário inválido: {form.errors}")
            messages.error(request, f"Erro ao validar o formulário: {form.errors}")

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
@check_group(["Administrador", "Confeitaria"])
def visualizar_ficha(request, ficha_id):
    """
    Visualiza uma ficha de produção do Firestore.
    """
    from confeitaria.repos_fichas import FichasRepo
    
    fichas_repo = FichasRepo()
    # Converte ficha_id para string (Firestore usa strings como IDs)
    ficha_dict = fichas_repo.get(str(ficha_id))
    
    if not ficha_dict:
        from django.http import Http404
        raise Http404("Ficha não encontrada no Firestore.")
    
    # Converte para objeto acessível
    ficha = SimpleNamespace(**ficha_dict)
    
    # Converte insumos para lista de objetos
    ficha_insumos = []
    for insumo_data in ficha_dict.get('insumos', []):
        insumo_obj = SimpleNamespace(**insumo_data)
        ficha_insumos.append(insumo_obj)
    
    return render(request, "core/ficha_detalhada.html", {
        "ficha": ficha, 
        "ficha_insumos": ficha_insumos
    })


@login_required
@check_group("Confeitaria")
def fichas_list(request):
    """Lista todas as fichas de produção do Firestore."""
    items = _FS_FICHAS.list(limit=1000)
    fichas = _wrap_dicts_as_objs(items)
    return render(request, "core/fichas_list.html", {"fichas": fichas})


@login_required
@check_group("Confeitaria")
def editar_ficha(request, id):
    """Edita uma ficha de produção no Firestore."""
    data = _FS_FICHAS.get_by_id(str(id))
    if not data:
        messages.error(request, "Ficha não encontrada.")
        return redirect("fichas_list")
    
    form = FichaProducaoForm(request.POST or None, initial=data)
    if request.method == "POST" and form.is_valid():
        cleaned = form.cleaned_data
@login_required
@check_group("Confeitaria")
def deletar_ficha(request, id):
    """Deleta uma ficha de produção do Firestore."""
    data = _FS_FICHAS.get_by_id(str(id))
    if not data:
        messages.error(request, "Ficha não encontrada.")
        return redirect("fichas_list")
    
    if request.method == "POST":
        _FS_FICHAS.delete(str(id))
        messages.success(request, "Ficha de produção deletada com sucesso!")
        return redirect("fichas_list")
    
    ficha = _wrap_dicts_as_objs([data])[0]
    return render(request, "core/delete.html", {"obj": ficha})
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
    """
    Lista produtos do catálogo - 100% FIRESTORE
    """
    from confeitaria.repos_catalogo import CatalogoRepo
    repo = CatalogoRepo()
    catalogo_list = repo.list(limit=1000)
    catalogo = _wrap_dicts_as_objs(catalogo_list)
    return render(request, "core/catalogo_list.html", {"catalogo": catalogo})


@login_required
@check_group("Administrador")
def catalogo_create(request):
    """
    Cria produto no catálogo - 100% FIRESTORE
    """
    if request.method == "POST":
        from confeitaria.repos_catalogo import CatalogoRepo
        repo = CatalogoRepo()
        
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        
        data = {
            'nome': nome,
            'descricao': descricao,
            'criado_em': timezone.now().isoformat()
        }
        repo.create_catalogo(data)
        messages.success(request, "Produto adicionado ao catálogo!")
        return redirect("catalogo_list")
    return render(request, "core/catalogo_form.html")


@login_required
@check_group("Administrador")
def catalogo_edit(request, pk):
    """
    Edita produto do catálogo - 100% FIRESTORE
    """
    from confeitaria.repos_catalogo import CatalogoRepo
    repo = CatalogoRepo()
    
    catalogo_data = repo.get(str(pk))
    if not catalogo_data:
        messages.error(request, "Produto não encontrado.")
        return redirect("catalogo_list")
    
    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        
        update_data = {
            **catalogo_data,
            'nome': nome,
            'descricao': descricao,
            'atualizado_em': timezone.now().isoformat()
        }
        repo.update_catalogo(str(pk), update_data)
        messages.success(request, "Produto atualizado com sucesso!")
        return redirect("catalogo_list")
    
    catalogo_item = SimpleNamespace(**catalogo_data)
    return render(request, "core/catalogo_form.html", {"catalogo": catalogo_item})


@login_required
@check_group("Administrador")
def catalogo_delete(request, id):
    """
    Deleta produto do catálogo - 100% FIRESTORE
    """
    from confeitaria.repos_catalogo import CatalogoRepo
    repo = CatalogoRepo()
    
    catalogo_data = repo.get(str(id))
    if not catalogo_data:
        messages.error(request, "Produto não encontrado.")
        return redirect("catalogo_list")
    
    if request.method == "POST":
        repo.delete(str(id))
        messages.success(request, "Produto do catálogo deletado!")
        return redirect("catalogo_list")
    
    item = SimpleNamespace(**catalogo_data)
    return render(request, "core/delete.html", {"obj": item})
