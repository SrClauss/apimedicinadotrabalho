from flask import Blueprint, request, jsonify, current_app
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from bcrypt import checkpw
import jwt
from datetime import datetime, timezone, timedelta  # Importação corrigida

# Criando o Blueprint para rotas de autenticação
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Autentica um usuário e retorna um token JWT
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email e senha são obrigatórios'}), 400

    db = get_db()
    
    # Verifica se é um usuário
    user = db.query(User).filter_by(email=data['email']).first()
    company = db.query(Company).filter_by(email=data['email']).first()
    
    if not user and not company:
        return jsonify({'message': 'Email ou senha inválidos'}), 404
    
    print("""
            
          """)
    if user and checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        token = jwt.encode({'sub': user.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, current_app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    
    if company and checkpw(data['password'].encode('utf-8'), company.password_hash.encode('utf-8')):   
        token = jwt.encode({'sub': company.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, current_app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    
    return jsonify({'message': 'Email ou senha inválidos'   }), 401
    

