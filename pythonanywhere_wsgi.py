"""
WSGI config for PythonAnywhere deployment.

Substitua o conteúdo do arquivo /var/www/seuusername_pythonanywhere_com_wsgi.py
no painel Web do PythonAnywhere com este código.
"""

import os
import sys

# Adicionar o diretório do projeto ao Python path
path = '/home/seuusername/gerenciamento'  # ⚠️ ALTERE 'seuusername' pelo seu username
if path not in sys.path:
    sys.path.insert(0, path)

# Ativar ambiente virtual
activate_this = '/home/seuusername/gerenciamento/venv/bin/activate_this.py'  # ⚠️ ALTERE 'seuusername'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confeitaria.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()