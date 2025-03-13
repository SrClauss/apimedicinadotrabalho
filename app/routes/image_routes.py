import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

image_bp = Blueprint('image', __name__)

# Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@image_bp.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        # Verifique se o request tem a parte do arquivo
        if 'imagem' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        file = request.files['imagem']

        # Se o usuário não selecionar um arquivo, o browser envia uma string vazia
        if file.filename == '':
            return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400

        # Verifique se o nome da imagem foi fornecido como parâmetro
        image_name = request.args.get('image_name')
        if not image_name:
            return jsonify({'erro': 'Nome da imagem não fornecido'}), 400

        if file and allowed_file(file.filename):
            # Garante que o nome do arquivo seja seguro e adiciona a extensão original
            filename = secure_filename(image_name + '.' + file.filename.rsplit('.', 1)[1].lower())
            # Use app.config['UPLOAD_FOLDER'] para obter o caminho do diretório de upload
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            return jsonify({'mensagem': 'Arquivo enviado com sucesso', 'filename': filename}), 200
        else:
            return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400

    except Exception as e:
        current_app.logger.error(f"Erro ao fazer upload da imagem: {str(e)}")
        return jsonify({'erro': 'Erro ao fazer upload da imagem'}), 500