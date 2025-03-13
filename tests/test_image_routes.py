import unittest
import json
import io
import os
import tempfile
from unittest.mock import patch, mock_open
from app import create_app
from werkzeug.datastructures import FileStorage

class ImageRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Criar pasta temporária para uploads
        self.test_upload_folder = tempfile.mkdtemp()
        
        # Criar aplicação de teste com configuração específica
        self.app = create_app(testing=True)
        self.app.config['UPLOAD_FOLDER'] = self.test_upload_folder
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpeza executada após cada teste"""
        # Remover arquivos temporários
        for filename in os.listdir(self.test_upload_folder):
            os.remove(os.path.join(self.test_upload_folder, filename))
        os.rmdir(self.test_upload_folder)
    
    def test_upload_image_success(self):
        """Teste de upload de imagem com sucesso"""
        # Criar dados de imagem simulada (bytes de um PNG válido)
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
            b'\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\r'
            b'IDAT\x08\xd7c````\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00'
            b'\x00\x00IEND\xaeB`\x82'
        )
        image = FileStorage(
            stream=io.BytesIO(image_data),
            filename='test_image.png',
            content_type='image/png'
        )
        
        # Fazer requisição POST para upload de imagem
        response = self.client.post(
            '/api/upload_image?image_name=perfil_teste',
            content_type='multipart/form-data',
            data={'imagem': image}
        )
        
        # Verificações
        self.assertEqual(response.status_code, 200)
        self.assertIn('mensagem', response.json)
        self.assertEqual(response.json['filename'], 'perfil_teste.png')
        
        # Verificar se o arquivo foi realmente salvo
        saved_file_path = os.path.join(self.test_upload_folder, 'perfil_teste.png')
        self.assertTrue(os.path.exists(saved_file_path))
    
    def test_upload_no_file(self):
        """Teste de upload sem arquivo"""
        response = self.client.post('/api/upload_image?image_name=test')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nenhum arquivo enviado', response.json['erro'])
    
    def test_upload_empty_filename(self):
        """Teste de upload com nome de arquivo vazio"""
        image_data = io.BytesIO(b'some image data')
        image = FileStorage(
            stream=image_data,
            filename='', 
            content_type='image/png'
        )
        
        response = self.client.post(
            '/api/upload_image?image_name=test',
            content_type='multipart/form-data',
            data={'imagem': image}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nenhum arquivo selecionado', response.json['erro'])
    
    def test_upload_no_image_name(self):
        """Teste de upload sem nome de imagem"""
        image_data = io.BytesIO(b'some image data')
        image = FileStorage(
            stream=image_data,
            filename='test.png', 
            content_type='image/png'
        )
        
        response = self.client.post(
            '/api/upload_image',
            content_type='multipart/form-data',
            data={'imagem': image}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nome da imagem não fornecido', response.json['erro'])
    
    def test_upload_invalid_extension(self):
        """Teste de upload com extensão não permitida"""
        image_data = io.BytesIO(b'some text data')
        image = FileStorage(
            stream=image_data,
            filename='test.txt', 
            content_type='text/plain'
        )
        
        response = self.client.post(
            '/api/upload_image?image_name=test',
            content_type='multipart/form-data',
            data={'imagem': image}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Tipo de arquivo não permitido', response.json['erro'])
    
    @patch('app.routes.image_routes.os.path.join')
    @patch('werkzeug.datastructures.FileStorage.save')
    def test_upload_exception(self, mock_save, mock_join):
        """Teste de upload com exceção durante salvamento"""
        # Configurar o mock para lançar uma exceção
        mock_join.return_value = '/tmp/fake_path'
        mock_save.side_effect = Exception('Erro ao salvar')
        
        # Criar dados falsos para simulação
        image_data = io.BytesIO(b'some image data')
        image = FileStorage(
            stream=image_data,
            filename='test.png', 
            content_type='image/png'
        )
        
        response = self.client.post(
            '/api/upload_image?image_name=test',
            content_type='multipart/form-data',
            data={'imagem': image}
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('Erro ao fazer upload', response.json['erro'])

if __name__ == '__main__':
    unittest.main()