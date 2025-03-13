import os
import sys
from importlib.machinery import SourceFileLoader

# Adiciona o diretório do arquivo atual ao PATH
sys.path.insert(0, os.path.dirname(__file__))

# Carrega o arquivo app.py dinamicamente
wsgi = SourceFileLoader('wsgi', 'app.py').load_module()

# Atribui a aplicação WSGI
application = wsgi.app