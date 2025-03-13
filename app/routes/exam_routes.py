from flask import Blueprint, render_template, request, jsonify, current_app
from app.models.exam import Exam
from app import get_db

exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/exames/criar', methods=['POST'])
def criar():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Nenhum dado de entrada fornecido"}), 400

        # Validação dos dados (pode ser mais completa)
        if 'title' not in data or 'company_id' not in data or 'user_id' not in data:
            return jsonify({"erro": "Título, company_id e user_id são obrigatórios"}), 400

        db = get_db()
        exam = Exam(
            title=data['title'],
            description=data.get('description'),  # Use .get para campos opcionais
            company_id=data['company_id'],
            user_id=data['user_id']
        )

        db.add(exam)
        db.commit()

        return jsonify({"mensagem": "Exame criado com sucesso", "id": exam.id}), 201
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao criar exame: {str(e)}")
        return jsonify({"erro": "Erro ao criar exame"}), 500

@exam_bp.route('/exames/obter/<id>', methods=['GET'])
def obter(id):
    try:
        db = get_db()
        exam = db.query(Exam).get(id)

        if not exam:
            return jsonify({"erro": "Exame não encontrado"}), 404

        return jsonify({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "company_id": exam.company_id,
            "user_id": exam.user_id
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao obter exame: {str(e)}")
        return jsonify({"erro": "Erro ao obter exame"}), 500

@exam_bp.route('/exames/atualizar/<id>', methods=['PUT'])
def atualizar(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Nenhum dado de entrada fornecido"}), 400

        db = get_db()
        exam = db.query(Exam).get(id)

        if not exam:
            return jsonify({"erro": "Exame não encontrado"}), 404

        # Atualiza os campos (pode ser feito de forma mais dinâmica)
        exam.title = data.get('title', exam.title)
        exam.description = data.get('description', exam.description)
        exam.company_id = data.get('company_id', exam.company_id)
        exam.user_id = data.get('user_id', exam.user_id)

        db.commit()

        return jsonify({"mensagem": "Exame atualizado com sucesso"}), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao atualizar exame: {str(e)}")
        return jsonify({"erro": "Erro ao atualizar exame"}), 500

@exam_bp.route('/exames/deletar/<id>', methods=['DELETE'])
def deletar(id):
    try:
        db = get_db()
        exam = db.query(Exam).get(id)

        if not exam:
            return jsonify({"erro": "Exame não encontrado"}), 404

        db.delete(exam)
        db.commit()

        return jsonify({"mensagem": "Exame excluído com sucesso"}), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Erro ao excluir exame: {str(e)}")
        return jsonify({"erro": "Erro ao excluir exame"}), 500

@exam_bp.route('/exames/listar', methods=['GET'])
def listar():
    try:
        db = get_db()
        exams = db.query(Exam).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames"}), 500

@exam_bp.route('/exames/listar_por_usuario/<user_id>', methods=['GET'])
def listar_por_usuario(user_id):
    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.user_id == user_id).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames por usuário: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por usuário"}), 500

@exam_bp.route('/exames/listar_por_empresa/<company_id>', methods=['GET'])
def listar_por_empresa(company_id):
    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.company_id == company_id).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames por empresa: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por empresa"}), 500

    
    #filtrar por data lembrando que base tem um campo created_at

@exam_bp.route('/exames/listar_por_data/<data>', methods=['GET'])
def listar_por_data(data):
    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.created_at == data).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames por data: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por data"}), 500

#filtrar por data e empresa, e outro filtro por data e usuario

@exam_bp.route('/exames/listar_por_data_empresa/<data>/<company_id>', methods=['GET'])
def listar_por_data_empresa(data, company_id):
    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.created_at == data, Exam.company_id == company_id).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames por data e empresa: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por data e empresa"}), 500


@exam_bp.route('/exames/listar_por_data_usuario/<data>/<user_id>', methods=['GET'])
def listar_por_data_usuario(data, user_id):

    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.created_at == data, Exam.user_id == user_id).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames por data e usuário: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por data e usuário"}), 500

@exam_bp.route('/exames/listar_por_data_usuario_empresa/<data>/<user_id>/<company_id>', methods=['GET'])

def listar_por_data_usuario_empresa(data, user_id, company_id):
    try:
        db = get_db()
        exams = db.query(Exam).filter(Exam.created_at == data, Exam.user_id == user_id, Exam.company_id == company_id).all()
        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "company_id": exam.company_id,
                "user_id": exam.user_id
            })
        return jsonify(exam_list), 200
    except Exception as e:

        current_app.logger.error(f"Erro ao listar exames por data, usuário e empresa: {str(e)}")
        return jsonify({"erro": "Erro ao listar exames por data, usuário e empresa"}), 500
@exam_bp.route('/upload', methods=['GET'])
def show_upload_form():
    return render_template('upload.html')