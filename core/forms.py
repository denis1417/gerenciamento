from django import forms
from django.contrib.auth.models import User
from .models import (
    FichaProducao,
    Colaborador,
    Insumo,
    ProdutoPronto,
    SaidaInsumo,
    CatalogoProduto
)


# ------------------ CRIAR USUÁRIO ------------------
# Nota: Formulário não usado - usuários são criados via template personalizado 
# que usa Firestore para buscar colaboradores


# ------------------ FICHA DE PRODUÇÃO ------------------


class FichaProducaoForm(forms.ModelForm):
    class Meta:
        model = FichaProducao
        fields = [
            "categoria",
            "data_fabricacao",
            "textura",
            "validade",
            "armazenamento",
            "calorias",
            "tempo_preparo",
            "perda_aceitavel",
            "rendimento",
            "observacoes",
            "peso_produto",
        ]
        widgets = {
            "data_fabricacao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "categoria": forms.TextInput(attrs={"class": "form-control"}),
            "textura": forms.TextInput(attrs={"class": "form-control"}),
            "validade": forms.NumberInput(attrs={"class": "form-control"}),
            "armazenamento": forms.TextInput(attrs={"class": "form-control"}),
            "calorias": forms.NumberInput(attrs={"class": "form-control"}),
            "tempo_preparo": forms.NumberInput(attrs={"class": "form-control"}),
            "perda_aceitavel": forms.TextInput(attrs={"class": "form-control"}),
            "rendimento": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "peso_produto": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
        }
        labels = {
            "peso_produto": "Peso do Produto (g)",
        }

    def __init__(self, *args, **kwargs):
        produto_presente = kwargs.pop("produto_presente", False)
        super().__init__(*args, **kwargs)
        # Apenas adiciona classes se não existir
        for visible in self.visible_fields():
            if not visible.field.widget.attrs.get("class"):
                visible.field.widget.attrs["class"] = "form-control"


# ------------------ INSUMO ------------------

class InsumoForm(forms.ModelForm):
    quantidade_principal = forms.FloatField(
        label="Quantidade Principal",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    quantidade_complementar = forms.FloatField(
        label="Complementar",
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Insumo
        fields = ['nome', 'unidade_base']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'unidade_base': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.unidade_base in ['g', 'ml']:
                self.fields['quantidade_principal'].initial = int(
                    self.instance.quantidade_total // 1000)
                self.fields['quantidade_complementar'].initial = self.instance.quantidade_total % 1000
            else:
                self.fields['quantidade_principal'].initial = self.instance.quantidade_total
                self.fields['quantidade_complementar'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        principal = cleaned_data.get('quantidade_principal') or 0
        complementar = cleaned_data.get('quantidade_complementar') or 0
        unidade = cleaned_data.get('unidade_base')

        if unidade in ['g', 'ml']:
            cleaned_data['quantidade_total'] = principal * 1000 + complementar
        else:
            cleaned_data['quantidade_total'] = principal + complementar

        return cleaned_data

    def save(self, commit=True):
        self.instance.quantidade_total = self.cleaned_data['quantidade_total']
        return super().save(commit=commit)


# ------------------ PRODUTO PRONTO ------------------

class ProdutoProntoForm(forms.Form):
    """Formulário para produto pronto - compatível com Firestore"""
    
    catalogo = forms.ChoiceField(
        label='Produto',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    quantidade = forms.IntegerField(
        label='Quantidade',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=True
    )
    data_fabricacao = forms.DateField(
        label='Data de Fabricação',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    data_validade = forms.DateField(
        label='Data de Validade',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    peso_produto = forms.DecimalField(
        label='Peso do Produto (g)',
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        required=True,
        decimal_places=2
    )
    
    def __init__(self, *args, use_firestore=True, **kwargs):
        # Remover 'instance' se vier nos kwargs (não é compatível com Form)
        if 'instance' in kwargs:
            instance = kwargs.pop('instance')
            # Se tem instance, preencher com initial
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            if hasattr(instance, 'catalogo_id'):
                kwargs['initial']['catalogo'] = instance.catalogo_id
            if hasattr(instance, 'quantidade'):
                kwargs['initial']['quantidade'] = instance.quantidade
            if hasattr(instance, 'data_fabricacao'):
                kwargs['initial']['data_fabricacao'] = instance.data_fabricacao
            if hasattr(instance, 'data_validade'):
                kwargs['initial']['data_validade'] = instance.data_validade
            if hasattr(instance, 'peso_produto'):
                kwargs['initial']['peso_produto'] = instance.peso_produto
        
        super().__init__(*args, **kwargs)
        
        # Carregar produtos do catálogo do Firestore
        try:
            from confeitaria.repos_catalogo import CatalogoRepo
            
            catalogo_repo = CatalogoRepo()
            produtos_fs = catalogo_repo.list(limit=1000)
            
            # Criar choices para o campo catálogo
            choices = [('', '---------')]
            for produto_data in produtos_fs:
                label = produto_data.get('nome', 'N/A')
                descricao = produto_data.get('descricao')
                if descricao:
                    label = f"{label} ({descricao})"
                choices.append((produto_data['id'], label))
            
            self.fields['catalogo'].choices = choices
            
        except Exception as e:
            print(f"Erro ao carregar produtos do Firestore: {e}")
            import traceback
            traceback.print_exc()


# ------------------ SAÍDA DE INSUMO ------------------
class SaidaInsumoForm(forms.ModelForm):
    quantidade = forms.FloatField(
        label="Quantidade",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SaidaInsumo
        fields = ['insumo', 'colaborador_entregando',
                  'colaborador_retira', 'unidade', 'quantidade']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'colaborador_entregando': forms.Select(attrs={'class': 'form-select'}),
            'colaborador_retira': forms.Select(attrs={'class': 'form-select'}),
            'unidade': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, use_firestore=False, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se usar Firestore, carregar insumos e colaboradores do Firestore
        if use_firestore:
            from confeitaria.repos_insumos import InsumosRepo
            from django import forms as django_forms
            
            # Buscar insumos do Firestore
            repo = InsumosRepo()
            insumos_fs = repo.list(limit=1000)
            
            # Criar choices para o campo insumo
            choices = [('', '---------')]
            for insumo_data in insumos_fs:
                # Formatação da quantidade para exibição
                qtd = float(insumo_data['quantidade_total'])
                unidade = insumo_data['unidade_base']
                
                if unidade == 'g' and qtd >= 1000:
                    display_qtd = f"({qtd/1000:.0f} kg {int(qtd%1000)} g)"
                elif unidade == 'ml' and qtd >= 1000:
                    display_qtd = f"({qtd/1000:.0f} L {int(qtd%1000)} ml)"
                else:
                    display_qtd = f"({int(qtd)} {unidade})"
                
                label = f"{insumo_data['nome']} {display_qtd}"
                choices.append((insumo_data['id'], label))
            
            # Substituir o campo insumo por um ChoiceField
            self.fields['insumo'] = django_forms.ChoiceField(
                choices=choices,
                widget=django_forms.Select(attrs={'class': 'form-select'}),
                label='Insumo'
            )
            
            # Carregar colaboradores do Firestore
            try:
                from confeitaria.repos_colaboradores import ColaboradoresRepo
                colab_repo = ColaboradoresRepo()
                colaboradores_fs = colab_repo.list(limit=1000)
                
                # Criar choices para colaborador_entregando
                colab_choices = [('', '---------')]
                for colab_data in colaboradores_fs:
                    label = f"{colab_data.get('nome', 'N/A')} ({colab_data.get('funcao', 'N/A')})"
                    colab_choices.append((colab_data['id'], label))
                
                # Substituir os campos de colaborador por ChoiceFields
                self.fields['colaborador_entregando'] = django_forms.ChoiceField(
                    choices=colab_choices,
                    widget=django_forms.Select(attrs={'class': 'form-select'}),
                    label='Colaborador Entregando',
                    required=True
                )
                
                self.fields['colaborador_retira'] = django_forms.ChoiceField(
                    choices=colab_choices,
                    widget=django_forms.Select(attrs={'class': 'form-select'}),
                    label='Colaborador que Retira',
                    required=True
                )
                
                # Também substituir o campo unidade por choices fixas
                unidade_choices = [
                    ('', '---------'),
                    ('g', 'gramas'),
                    ('ml', 'mililitros'),
                    ('un', 'unidades'),
                ]
                self.fields['unidade'] = django_forms.ChoiceField(
                    choices=unidade_choices,
                    widget=django_forms.Select(attrs={'class': 'form-select'}),
                    label='Unidade',
                    required=True
                )
                
            except Exception:
                # Se falhar ao carregar colaboradores do Firestore, mantém comportamento original
                pass

    def save(self, commit=True):
        # IMPORTANTE: Só salva no banco se NÃO estivermos usando Firestore
        # No modo Firestore, este método não deveria ser chamado
        if hasattr(self, '_use_firestore') and self._use_firestore:
            # Não salva quando estamos usando Firestore
            return None
        
        # Salva diretamente em quantidade_principal e zera complementar
        self.instance.quantidade_principal = self.cleaned_data['quantidade']
        self.instance.quantidade_complementar = 0
        return super().save(commit=commit)


# ------------------ COLABORADOR ------------------
class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = [
            'rc',
            'nome',
            'data_nascimento',
            'sexo',
            'funcao',
            'CPF_RG',
            'foto',
            'email',
            'celular',
            'cep',
            'logradouro',
            'numero',
            'bairro',
            'cidade',
            'estado',
            'complemento',
            'usuario',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control'}),
            'CPF_RG': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
        }
