from flask import Blueprint, request, jsonify, current_app, url_for
from app.models.company import Company
from app.models.user import User, PendingUser, UserDTO
from app import get_db, mail
from flask_mail import Message
from bcrypt import hashpw, gensalt
from datetime import datetime, timedelta

user_bp = Blueprint('user', __name__)

def enviar_email(para, assunto, template):
    try:
        msg = Message(assunto, recipients=[para], html=template, sender=current_app.config['MAIL_USERNAME'])
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar e-mail: {str(e)}")
        raise

def enviar_email_verificacao(user_dto: UserDTO):
    try:
        token = user_dto.to_jwt()
        confirm_url = url_for('user_blueprint.confirmar', token=token, _external=True)
        html = f'<b>Bem-vindo! Por favor, confirme seu e-mail clicando <a href="{confirm_url}">aqui</a>.</b>'
        assunto = "Por favor, confirme seu e-mail"
        enviar_email(user_dto.email, assunto, html)
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar e-mail de verificação: {str(e)}")
        raise

@user_bp.route('/usuario/registrar', methods=['POST'])
def registrar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado de entrada fornecido"}), 400

        # Verifica se o e-mail já está registrado ou pendente
        db = get_db()
        
        existing_user = db.query(User).filter(User.email == dados['email']).first()
        existing_company = db.query(Company).filter(Company.email == dados['email']).first()
        
        
        
        if existing_user or existing_company:
            return jsonify({"erro": "E-mail já registrado ou pendente de confirmação"}), 400
        
        
        existing_pending = db.query(PendingUser).filter(PendingUser.email == dados['email']).first()
        
        if existing_user or existing_pending:
            return jsonify({"erro": "E-mail já registrado ou pendente de confirmação"}), 400
        # Cria um PendingUser temporário
        pending_user = PendingUser(
            name=dados['name'],
            email=dados['email'],
            address=dados['address'],
            phone=dados['phone'],
            cpf=dados['cpf'],           
            password_hash=hashpw(dados['password'].encode('utf-8'), gensalt()).decode('utf-8')

        )

        db.add(pending_user)
        db.commit()

        # Envia o e-mail de confirmação
        user_dto = UserDTO(email=pending_user.email)
        enviar_email_verificacao(user_dto)

        return jsonify({"mensagem": "Verifique seu e-mail para confirmar a conta."}), 201
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao registrar usuário: {str(e)}")
        return jsonify({"erro": "Erro ao registrar usuário"}), 500

@user_bp.route('/usuario/confirmar/<token>', methods=['GET'])
def confirmar(token):
    try:
        user_dto = UserDTO.from_jwt(token)
        if not user_dto:
            return jsonify({"erro": "Token inválido ou expirado"}), 400

        db = get_db()

        # Busca o PendingUser correspondente
        #pending_user = PendingUser.query.filter_by(email=user_dto.email).first()
        pending_user = db.query(PendingUser).filter(PendingUser.email == user_dto.email).first()
        if not pending_user:
            return jsonify({"erro": "Registro pendente não encontrado"}), 404

        # Cria o usuário final
        user = User(
            name=pending_user.name,
            email=pending_user.email,
            password_hash=pending_user.password_hash,
         
        )

        db.add(user)
        db.delete(pending_user)  # Remove o registro pendente
        db.commit()

        return jsonify({"mensagem": "Conta confirmada com sucesso!"}), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao confirmar e-mail: {str(e)}")
        return jsonify({"erro": "Erro ao confirmar e-mail"}), 500

@user_bp.route('/usuario/redefinir_senha', methods=['POST'])
def redefinir_senha():
    try:
        dados = request.get_json()
        if not dados or 'email' not in dados:
            return jsonify({"erro": "Nenhum e-mail fornecido"}), 400

        email = dados['email']
        db = get_db()
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return jsonify({"erro": "Usuário não encontrado"}), 404

        user_dto = UserDTO(
            email=user.email,
            name=user.name,
            password=None,
            address=user.address,
            phone=user.phone,
            cpf=user.cpf
            
        )
        token = user_dto.to_jwt()
        reset_url = url_for('user_blueprint.confirmar_redefinicao', token=token, _external=True)
        html = f'<b>Para redefinir sua senha, clique <a href="{reset_url}">aqui</a>.</b>'
        assunto = "Redefinição de senha"
        enviar_email(user.email, assunto, html)
        return jsonify({"mensagem": "E-mail de redefinição de senha enviado com sucesso."}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar e-mail de redefinição de senha: {str(e)}")
        return jsonify({"erro": "Erro ao enviar e-mail de redefinição de senha"}), 500

@user_bp.route('/usuario/confirmar_redefinicao/<token>', methods=['GET'])
def confirmar_redefinicao(token):
    try:
        user_dto = UserDTO.from_jwt(token)
        if not user_dto:
            return jsonify({"erro": "Token inválido ou expirado"}), 400

        return jsonify({
            "mensagem": "Link de redefinição válido. Por favor, redefina sua senha.",
            "email": user_dto.email
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao processar token de redefinição de senha: {str(e)}")
        return jsonify({"erro": "Erro ao processar token de redefinição de senha"}), 500
    
@user_bp.route('/usuario/limpar_pendentes', methods=['DELETE'])
def limpar_pendentes():
    try:
        db = get_db()
        # Define o limite de expiração como uma hora atrás
        limite_expiracao = datetime.utcnow() - timedelta(hours=1)
        # Remove todos os registros expirados
        expirados = db.query(PendingUser).filter(PendingUser.expiration < limite_expiracao).all()
        for pendente in expirados:
            db.delete(pendente)
        db.commit()
        return jsonify({"mensagem": f"{len(expirados)} registros expirados removidos."}), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao limpar pending_users: {str(e)}")
        return jsonify({"erro": "Erro ao limpar registros expirados"}), 500
    
@user_bp.route('/usuario/obter/<id>', methods=['GET'])
def obter(id):
    try:
        db = get_db()
        user = db.query(User).get(id)

        if not user:
            return jsonify({"erro": "Usuário não encontrado"}), 404

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao obter usuário: {str(e)}")
        return jsonify({"erro": "Erro ao obter usuário"}), 500
    

@user_bp.route('/usuarios/find_by_substring/<substring>', methods=['GET'])
def find_by_substring(substring):
    try:
        db = get_db()
        users = db.query(User).filter(User.name.contains(substring)).all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
               
            })
        return jsonify(user_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar usuários por substring: {str(e)}")
        return jsonify({"erro": "Erro ao buscar usuários por substring"}), 500

@user_bp.route('/usuario/nova_senha', methods=['PUT'])
def nova_senha():
    try:
        dados = request.get_json()
        if not dados or 'email' not in dados or 'password' not in dados:
            return jsonify({"erro": "E-mail e nova senha são obrigatórios"}), 400

        email = dados['email']
        db = get_db()
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return jsonify({"erro": "Usuário não encontrado"}), 404

        user.password_hash = hashpw(dados['password'].encode('utf-8'), gensalt()).decode('utf-8')
        db.commit()
        return jsonify({"mensagem": "Senha alterada com sucesso"}), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao alterar senha: {str(e)}")
        return jsonify({"erro": "Erro ao alterar senha"}), 500