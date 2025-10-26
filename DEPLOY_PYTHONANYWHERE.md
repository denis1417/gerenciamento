# 🐍 Deploy no PythonAnywhere - Guia Completo

## 🎯 Vantagens para seu Projeto

### ✅ **Por que PythonAnywhere é Perfeito:**
- **SQLite nativo**: Arquivos persistem entre deployments
- **Django especializado**: Configuração otimizada
- **Firestore compatível**: Google Cloud funciona perfeitamente
- **Interface amigável**: Tudo via web, sem terminal complexo
- **Preço justo**: $5/mês ou gratuito (limitado)

## 📋 Passo a Passo Completo

### **1. Criar Conta**
- Acesse [pythonanywhere.com](https://www.pythonanywhere.com)
- Crie conta gratuita ou paga
- Acesse o Dashboard

### **2. Configurar Projeto**

#### **2.1 Console Bash**
```bash
# Abrir console Bash no painel
cd ~
git clone https://github.com/denis1417/gerenciamento.git
cd gerenciamento
git checkout feature/sistema-hibrido-firestore

# Criar ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### **2.2 Configurar Environment**
```bash
# Copiar exemplo
cp .env.example .env

# Editar configurações (usar editor do PythonAnywhere)
# Configurar:
# - SECRET_KEY=nova-chave-segura
# - DEBUG=False  
# - ALLOWED_HOSTS=seuusername.pythonanywhere.com
# - USE_FIRESTORE=True
```

#### **2.3 Upload Credenciais Firestore**
1. **Files tab** no painel PythonAnywhere
2. Navegar para `/home/seuusername/gerenciamento/secrets/`
3. **Upload** do arquivo `django-firestore-key.json`
4. Verificar permissões: `chmod 600 secrets/django-firestore-key.json`

#### **2.4 Setup Database**
```bash
# Ativar ambiente
source ~/gerenciamento/venv/bin/activate
cd ~/gerenciamento

# Migrations
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar admin (opcional)
python manage.py createsuperuser
```

### **3. Configurar Web App**

#### **3.1 Criar Web App**
1. **Web tab** no painel
2. **Add a new web app**
3. **Manual configuration**
4. **Python 3.12**

#### **3.2 Configurar WSGI**
1. **Code section** → **WSGI configuration file**
2. Substituir conteúdo por:

```python
import os
import sys

# Alterar 'seuusername' pelo seu username real
path = '/home/seuusername/gerenciamento'
if path not in sys.path:
    sys.path.insert(0, path)

# Ativar ambiente virtual  
activate_this = '/home/seuusername/gerenciamento/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confeitaria.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### **3.3 Configurar Diretórios**
- **Source code**: `/home/seuusername/gerenciamento`
- **Virtualenv**: `/home/seuusername/gerenciamento/venv`

#### **3.4 Configurar Static Files**
- **URL**: `/static/`
- **Directory**: `/home/seuusername/gerenciamento/staticfiles/`

- **URL**: `/media/`  
- **Directory**: `/home/seuusername/gerenciamento/media/`

### **4. Teste e Deploy**

#### **4.1 Reload**
- **Web tab** → **Reload** button
- Aguardar reload completo

#### **4.2 Verificar**
- Acessar `https://seuusername.pythonanywhere.com`
- Testar login admin
- Testar funcionalidades Firestore

#### **4.3 Troubleshooting**
- **Error logs**: Web tab → Error log
- **Server logs**: Web tab → Server log  
- **Console test**: `python manage.py runserver` no bash

## 🔧 Configurações Específicas

### **Firestore no PythonAnywhere**
```bash
# Testar conexão Firestore
cd ~/gerenciamento
source venv/bin/activate
python manage.py shell

>>> from confeitaria.repos_colaboradores import ColaboradoresRepo
>>> repo = ColaboradoresRepo()
>>> repo.list(limit=1)  # Deve funcionar
```

### **Variáveis de Ambiente**
No arquivo `.env`:
```env
SECRET_KEY=sua-chave-super-segura-aqui-pythonanywhere
DEBUG=False
ALLOWED_HOSTS=seuusername.pythonanywhere.com,localhost
USE_FIRESTORE=True
GOOGLE_CLOUD_PROJECT=projeto-integrador-2-31637
GOOGLE_APPLICATION_CREDENTIALS=/home/seuusername/gerenciamento/secrets/django-firestore-key.json
```

## 💡 Dicas Importantes

### **Plano Gratuito vs Pago**
- **Gratuito**: Limitado, mas funcional para testes
- **Hacker ($5/mês)**: Recomendado, sem limitações importantes
- **Domínio**: `seuusername.pythonanywhere.com` sempre incluído

### **Performance**
- **SQLite**: Rápido para desenvolvimento/testes
- **Firestore**: Produção real, escalável
- **Sistema híbrido**: Melhor dos dois mundos

### **Backup**
- **Código**: Git automático
- **SQLite**: Download via Files tab
- **Firestore**: Backup nativo do Google Cloud

## 🚀 URL Final
Sua aplicação ficará em: `https://seuusername.pythonanywhere.com`

## ✅ Checklist Deploy
- [ ] Conta PythonAnywhere criada
- [ ] Código clonado e venv configurado
- [ ] Credenciais Firestore uploaded
- [ ] .env configurado
- [ ] Migrations executadas
- [ ] Static files coletados
- [ ] WSGI configurado
- [ ] Web app reload
- [ ] Teste funcionando