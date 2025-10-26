# 🚀 Deploy do Sistema Híbrido SQLite/Firestore

## 📋 Pré-requisitos

1. **Credenciais do Google Cloud Firestore**
   - Acesse o [Google Cloud Console](https://console.cloud.google.com/)
   - Crie/acesse o projeto `projeto-integrador-2-31637`
   - Ative a API Firestore
   - Crie uma Service Account com permissões Firestore
   - Baixe o arquivo JSON das credenciais

## 🎯 Deploy Recomendado: Railway.app

### Passo 1: Preparação
```bash
# Clone o repositório
git clone https://github.com/denis1417/gerenciamento.git
cd gerenciamento

# Crie branch de produção (opcional)
git checkout feature/sistema-hibrido-firestore
```

### Passo 2: Railway Deploy
1. Acesse [railway.app](https://railway.app)
2. Conecte com GitHub
3. Selecione o repositório `gerenciamento`
4. Branch: `feature/sistema-hibrido-firestore`

### Passo 3: Configurar Variáveis de Ambiente
```env
SECRET_KEY=sua-chave-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=seu-projeto.railway.app
USE_FIRESTORE=True
GOOGLE_CLOUD_PROJECT=projeto-integrador-2-31637
```

### Passo 4: Configurar Credenciais Firestore
**Opção A: Upload do arquivo JSON**
- No Railway, vá em Variables
- Adicione `GOOGLE_APPLICATION_CREDENTIALS=/tmp/firestore-key.json`
- Faça upload do arquivo JSON para `/tmp/firestore-key.json`

**Opção B: JSON inline (mais fácil)**
- Copie todo o conteúdo do arquivo JSON das credenciais
- No Railway, crie variável `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- Cole o JSON completo como valor

### Passo 5: Deploy Automático
- Railway detectará o Procfile e fará deploy automático
- Acesse a URL fornecida pelo Railway

## 🔧 Configurações de Produção

### Firestore
- ✅ Banco principal em produção
- ✅ Suporte completo a CRUD
- ✅ Performance otimizada

### SQLite  
- ✅ Backup local dos dados
- ✅ Compatibilidade total
- ✅ Fallback automático

## 🧪 Teste Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar env
cp .env.example .env
# Editar .env com suas configurações

# Rodar migrations
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Rodar servidor
python manage.py runserver
```

## 📱 URLs da Aplicação

- **Admin**: `/admin/`
- **Home**: `/`
- **Colaboradores**: `/colaboradores/`
- **Firestore Test**: `/firestore/ping/`

## 🔐 Login de Teste

Criar superuser após deploy:
```bash
python manage.py createsuperuser
```

## 🚨 Troubleshooting

### Erro de Firestore
- Verificar credenciais do Google Cloud
- Confirmar que projeto existe
- Checar permissões da Service Account

### Erro de Static Files
- Verificar configuração STATIC_ROOT
- Executar `collectstatic` no deploy

### Erro 500
- Ativar DEBUG=True temporariamente
- Verificar logs do Railway
- Confirmar todas as env vars