import unittest
import json
from flask import Flask, g
from bcrypt import hashpw, gensalt
from unittest.mock import patch
from app import create_app, drop_test_db
from app.database import Base, get_db
from app.models.user import User
from app import TestSession

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Limpar o banco de dados de teste
        drop_test_db()
        
        # Configurar o banco de dados de teste
        self.db = TestSession()
        Base.metadata.create_all(bind=self.db.bind)
        
        # Criar um usuário de teste
        test_user = User(
            name="Test User",
            email="user@email.com",
            password_hash=hashpw("123456".encode("utf-8"), gensalt()).decode("utf-8"),
            address="Rua Teste, 123",
            phone="123456789",
            cpf="12345678901",
            role=0
        )
        
        # Adicionar o usuário ao banco de dados
        self.db.add(test_user)
        self.db.commit()
        
    def tearDown(self):
        """Limpeza executada após cada teste"""
        self.db.close()
        drop_test_db()
        
    @patch('app.routes.login.get_db')
    def test_login_success(self, mock_get_db):
        """Teste de login com sucesso"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar a aplicação de teste depois de configurar o mock
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer uma requisição POST para a rota de login
            response = client.post(
                "/api/login",
                data=json.dumps({"email": "user@email.com", "password": "123456"}),
                content_type="application/json",
            )
            
            # Verificar se o status code é 200 (OK)
            self.assertEqual(response.status_code, 200)
            
            # Verificar se a resposta contém um token
            data = json.loads(response.data)
            self.assertIn("token", data)
    
    @patch('app.routes.login.get_db')
    def test_login_wrong_password(self, mock_get_db):
        """Teste de login com senha incorreta"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar a aplicação de teste depois de configurar o mock
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            response = client.post(
                "/api/login",
                data=json.dumps({"email": "user@email.com", "password": "senha_errada"}),
                content_type="application/json",
            )
            
            # Verificar se o status code é 401 (Unauthorized)
            self.assertEqual(response.status_code, 401)

    @patch('app.routes.login.get_db')
    def test_login_user_not_found(self, mock_get_db):
        """Teste de login com usuário inexistente"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar a aplicação de teste depois de configurar o mock
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            response = client.post(
                "/api/login",
                data=json.dumps({"email": "naoexiste@email.com", "password": "123456"}),
                content_type="application/json",
            )
            
            # Verificar se o status code é 404 (Not Found)
            self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()