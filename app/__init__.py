# app/__init__.py
from flask import Flask
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from bcrypt import hashpw, gensalt
import ulid
import os
from datetime import datetime
from wtforms import validators
from wtforms.fields import StringField, PasswordField
from wtforms.widgets import PasswordInput
from wtforms import SelectField
from app.database import get_db, init_db
from app.models.company import PendingCompany
from app.models.user import PendingUser

# Configuração do banco de dados
DATABASE_URL = 'sqlite:///database.db'
TEST_DATABASE_URL = 'sqlite:///test_database.db'
test_engine = create_engine(TEST_DATABASE_URL)
engine = create_engine(DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))
TestSession = scoped_session(sessionmaker(bind=test_engine))

# Configuração do Flask-Mail
mail = Mail()

# Variável global para a aplicação
app = None

def create_app(testing=False):
    global app
    app = Flask(__name__)
    app.config['MAIL_SERVER'] = 'mail.giftxz.top'  # Servidor SMTP
    app.config['MAIL_PORT'] = 587  # Porta SMTP
    app.config['MAIL_USE_TLS'] = True  # Use TLS
    app.config['MAIL_USE_SSL'] = False  # Não use SSL
    app.config['MAIL_USERNAME'] = 'cadastro@giftxz.top'  # Seu e-mail
    app.config['MAIL_PASSWORD'] = 'DY213y1984'  # Sua senha de e-mail
    app.config['SECRET_KEY'] = 'VH-ar140la123fe0404'  # Sua chave secreta
    
    
    if testing:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URL
        app.config['SECRET_KEY'] = 'chave_teste'
    mail.init_app(app)

    # Configuração do diretório de upload de imagens
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, UPLOAD_FOLDER)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crie o diretório se não existir

    # Importar modelos após a criação do app para evitar importação circular
    from app.models.user import User
    from app.models.company import Company
    from app.models.exam import Exam

    class CustomAdminIndexView(AdminIndexView):
        def __init__(self, name=None, endpoint=None, url=None):
            super(CustomAdminIndexView, self).__init__(name='Home', endpoint='admin', url='/admin')
        
        @expose('/')
        def index(self):
            # Use a sessão SQLAlchemy diretamente
            db = get_db(testing=testing)
            return self.render('admin/index.html', stats={
                'users': db.query(User).count(),
                'companies': db.query(Company).count(),
                'exams': db.query(Exam).count()
            })

    # Altere a inicialização do Admin para usar a view personalizada
    admin = Admin(app, 
                  name='Admin Panel', 
                  template_mode='bootstrap4',
                  index_view=CustomAdminIndexView())

    class BaseModelView(ModelView):
        column_list = ['id', 'created_at', 'updated_at']
        form_excluded_columns = ['id', 'created_at', 'updated_at']
        
        def on_model_change(self, form, model, is_created):
            if is_created:
                if not model.id:
                    model.id = str(ulid.new())
                model.created_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            return super(BaseModelView, self).on_model_change(form, model, is_created)

    class UserModelView(BaseModelView):
        column_list = ['id', 'name', 'email', 'phone', 'address', 'cpf', 'role', 'created_at', 'updated_at']
        form_excluded_columns = ['id', 'created_at', 'updated_at', 'password_hash']

        form_extra_fields = {
            'name': StringField('name', [validators.DataRequired()]),
            'email': StringField('Email', [validators.DataRequired(), validators.Email()]),
            'phone': StringField('Phone', [validators.DataRequired()]),
            'address': StringField('Address', [validators.DataRequired()]),
            'cpf': StringField('CPF', [validators.DataRequired()]),
            'password': PasswordField('Password', widget=PasswordInput()),
            'role': SelectField('Função', choices=[(0, 'Admin'), (1, 'Editor'), (3, 'Worker')], 
                            coerce=int, default=3)
        }

        column_labels = {
            'name': 'Nome de Usuário',
            'email': 'E-mail',
            'phone': 'Telefone',
            'address': 'Endereço',
            'cpf': 'CPF',
            'role': 'Função',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em'
        }

        def on_model_change(self, form, model, is_created):
            # Garantir que o role seja definido corretamente
            if hasattr(form, 'role'):
                model.role = int(form.role.data)

            # Processar a senha
            if hasattr(form, 'password') and form.password.data:
                model.password_hash = hashpw(form.password.data.encode('utf-8'), gensalt()).decode('utf-8')

            return super(UserModelView, self).on_model_change(form, model, is_created)

    class CompanyModelView(BaseModelView):
        column_list = ['id', 'name', 'email', 'phone', 'address', 'cnpj', 'created_at', 'updated_at']
        form_excluded_columns = ['id', 'created_at', 'updated_at', 'password_hash']

        form_extra_fields = {
            'name': StringField('Name', [validators.DataRequired()]),
            'email': StringField('Email', [validators.DataRequired(), validators.Email()]),
            'phone': StringField('Phone', [validators.DataRequired()]),
            'address': StringField('Address', [validators.DataRequired()]),
            'cnpj': StringField('CNPJ', [validators.DataRequired()]),
            'password': PasswordField('Password', widget=PasswordInput())
        }

        column_labels = {
            'name': 'Nome',
            'email': 'E-mail',
            'phone': 'Telefone',
            'address': 'Endereço',
            'cnpj': 'CNPJ',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em'
        }

        def on_model_change(self, form, model, is_created):
            if hasattr(form, 'password') and form.password.data:
                model.password_hash = hashpw(form.password.data.encode('utf-8'), gensalt()).decode('utf-8')
            return super(CompanyModelView, self).on_model_change(form, model, is_created)
    
    class ExamModelView(BaseModelView):
        column_list = ['id', 'title', 'description', 'user', 'company', 'created_at', 'updated_at']
        form_excluded_columns = ['id', 'created_at', 'updated_at']
        
        # Configuração para exibir relacionamentos
        column_display_pk = True
        
        # Formatação para exibição de foreign keys
        column_formatters = {
            'user': lambda v, c, m, p: m.user.name if m.user else '',
            'company': lambda v, c, m, p: m.company.name if m.company else ''
        }
        
        # Adicione campos para título e descrição
        form_extra_fields = {
            'title': StringField('Título', [validators.DataRequired()]),
            'description': StringField('Descrição', [validators.DataRequired()]),
        }
        
        column_labels = {
            'title': 'Título',
            'description': 'Descrição',
            'user': 'Usuário',
            'company': 'Empresa',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em'
        }
        
        form_ajax_refs = {
            'user': {
                'fields': ['name', 'email'],
                'page_size': 10
            },
            'company': {
                'fields': ['name', 'email'],
                'page_size': 10
            }
        }

    class PendingUserModelView(BaseModelView):
        column_list = ['id', 'name', 'email', 'phone', 'address', 'cpf', 'expiration']
        form_excluded_columns = ['id', 'expiration']

        column_labels = {
            'name': 'Nome',
            'email': 'E-mail',
            'phone': 'Telefone',
            'address': 'Endereço',
            'cpf': 'CPF',
            'expiration': 'Expira em'
        }
    class PendingCompanyModelView(BaseModelView):
        column_list = ['id', 'name', 'email', 'phone', 'address', 'cnpj', 'expiration']
        form_excluded_columns = ['id', 'expiration']

        column_labels = {
            'name': 'Nome',
            'email': 'E-mail',
            'phone': 'Telefone',
            'address': 'Endereço',
            'cnpj': 'CNPJ',
            'expiration': 'Expira em'
        }
    # Adicionando os modelos ao painel administrativo
    db = get_db(testing=testing)
    # Corrija estas linhas removendo .session
    admin.add_view(UserModelView(User, db, name='user', endpoint='user'))
    admin.add_view(CompanyModelView(Company, db, name='company', endpoint='company'))
    admin.add_view(ExamModelView(Exam, db, name='exam', endpoint='exam'))
    admin.add_view(PendingUserModelView(PendingUser, db, name='pending_user', endpoint='pending_user'))
    admin.add_view(PendingCompanyModelView(PendingCompany, db, name='pending_company', endpoint='pending_company'))
    # Inicializar o banco de dados após a criação do app
    init_db()

    # Registrar blueprints com nomes únicos
    from app.routes.user_routes import user_bp
    from app.routes.company_routes import company_bp
    from app.routes.exam_routes import exam_bp
    from app.routes.image_routes import image_bp
  
    from app.routes.login import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api', name='auth')
    app.register_blueprint(user_bp, url_prefix='/api', name='user_blueprint')
    app.register_blueprint(company_bp, url_prefix='/api', name='company_blueprint')
    app.register_blueprint(exam_bp, url_prefix='/api', name='exam_blueprint')
    app.register_blueprint(image_bp, url_prefix='/api')

    return app

def get_db(testing=False):
    if testing:
        return TestSession()
    return Session()

def init_db(testing=False):
    
    
    
    """Inicializa o banco de dados criando todas as tabelas"""
    from app.models.user import Base
    from app.models.company import Base
    from app.models.exam import Base
    
    
    if testing:
        Base.metadata.create_all(bind=test_engine)
        return
    Base.metadata.create_all(bind=engine)
def drop_test_db():
    
    from app.models.user import Base
    from app.models.company import Base
    from app.models.exam import Base
    Base.metadata.drop_all(bind=test_engine)