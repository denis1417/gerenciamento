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


class CriarUsuarioForm(forms.ModelForm):
    colaborador = forms.ModelChoiceField(
        queryset=Colaborador.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Colaborador"
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'colaborador']


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

class ProdutoProntoForm(forms.ModelForm):
    class Meta:
        model = ProdutoPronto
        fields = ['catalogo', 'quantidade', 'data_fabricacao',
                  'data_validade', 'peso_produto']
        widgets = {
            'catalogo': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_fabricacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'peso_produto': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }
        labels = {
            'catalogo': 'Produto',
            'peso_produto': 'Peso do Produto (g)',
        }


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

    def save(self, commit=True):
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
