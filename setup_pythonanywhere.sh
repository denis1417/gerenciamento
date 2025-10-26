#!/bin/bash
# Setup script para PythonAnywhere

echo "🚀 Configurando aplicação Django no PythonAnywhere..."

# 1. Clone do repositório
echo "📥 Clonando repositório..."
git clone https://github.com/denis1417/gerenciamento.git
cd gerenciamento
git checkout feature/sistema-hibrido-firestore

# 2. Criar ambiente virtual
echo "🐍 Criando ambiente virtual..."
python3.12 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
echo "⚙️ Configurando environment..."
cp .env.example .env
echo "✏️ EDITE o arquivo .env com suas configurações!"

# 5. Migrations
echo "🗃️ Executando migrations..."
python manage.py migrate

# 6. Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# 7. Criar superuser (opcional)
echo "👤 Criar superuser? (opcional)"
# python manage.py createsuperuser

echo "✅ Setup concluído!"
echo "📝 Próximos passos:"
echo "1. Editar .env com suas configurações"
echo "2. Fazer upload das credenciais Firestore"
echo "3. Configurar Web App no painel PythonAnywhere"