import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from bcrypt import hashpw, gensalt, checkpw
from app import create_app, drop_test_db
from app.database import Base
from app.models.company import Company, PendingCompany, CompanyDTO
from app import TestSession

class CompanyRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Limpar o banco de dados de teste
        drop_test_db()
        
        # Configurar o banco de dados de teste
        self.db = TestSession()
        Base.metadata.create_all(bind=self.db.bind)
        
    def tearDown(self):
        """Limpeza executada após cada teste"""
        self.db.close()
        drop_test_db()
        
    @patch('app.routes.company_routes.get_db')
    @patch('app.routes.company_routes.enviar_email')
    def test_registrar_empresa(self, mock_enviar_email, mock_get_db):
        """Teste de registro de empresa"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Dados para registro
            dados_empresa = {
                "name": "Empresa Teste",
                "address": "Rua Teste, 123",
                "phone": "12345678901",
                "cnpj": "12345678901234",
                "email": "empresa@teste.com",
                "password": "senha123"
            }
            
            # Fazer requisição POST para registrar empresa
            response = client.post(
                "/api/empresa/registrar",
                data=json.dumps(dados_empresa),
                content_type="application/json"
            )
            
            # Verificações
            self.assertEqual(response.status_code, 201)
            self.assertIn("Verifique seu e-mail", response.json["mensagem"])
            
            # Verificar se o mock de enviar_email foi chamado
            mock_enviar_email.assert_called_once()
            
            # Verificar se a empresa pendente foi criada no banco
            empresa_pendente = self.db.query(PendingCompany).filter_by(email="empresa@teste.com").first()
            self.assertIsNotNone(empresa_pendente)
            self.assertEqual(empresa_pendente.name, "Empresa Teste")
    
    @patch('app.routes.company_routes.get_db')
    def test_registrar_empresa_email_existente(self, mock_get_db):
        """Teste de registro com email já existente"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar uma empresa existente
        empresa = Company(
            name="Empresa Existente",
            address="Rua Existente, 123",
            phone="11111111111",
            cnpj="11111111111111",
            email="empresa@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        self.db.add(empresa)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Dados para registro com mesmo email
            dados_empresa = {
                "name": "Outra Empresa",
                "address": "Outro Endereço, 456",
                "phone": "22222222222",
                "cnpj": "22222222222222",
                "email": "empresa@teste.com",
                "password": "outrasenha"
            }
            
            # Fazer requisição POST para registrar empresa
            response = client.post(
                "/api/empresa/registrar",
                data=json.dumps(dados_empresa),
                content_type="application/json"
            )
            
            # Verificar que retornou erro 400
            self.assertEqual(response.status_code, 400)
            self.assertIn("já registrado", response.json["erro"])
    
    @patch('app.routes.company_routes.get_db')
    @patch('app.routes.company_routes.CompanyDTO.from_jwt')
    def test_confirmar_empresa(self, mock_from_jwt, mock_get_db):
        """Teste de confirmação de empresa"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar uma empresa pendente
        empresa_pendente = PendingCompany(
            name="Empresa Pendente",
            address="Rua Pendente, 123",
            phone="33333333333",
            cnpj="33333333333333",
            email="pendente@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        self.db.add(empresa_pendente)
        self.db.commit()
        
        # Configurar o mock de from_jwt para retornar um CompanyDTO
        company_dto = CompanyDTO(
            name="Empresa Pendente",
            address="Rua Pendente, 123",
            phone="33333333333",
            cnpj="33333333333333", 
            email="pendente@teste.com",
            password=None
        )
        mock_from_jwt.return_value = company_dto
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para confirmar empresa (o token é mock)
            response = client.get("/api/empresa/confirmar/token_falso")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertIn("Conta confirmada", response.json["mensagem"])
            
            # Verificar se a empresa foi criada e a pendente removida
            empresa = self.db.query(Company).filter_by(email="pendente@teste.com").first()
            self.assertIsNotNone(empresa)
            
            pendente = self.db.query(PendingCompany).filter_by(email="pendente@teste.com").first()
            self.assertIsNone(pendente)
    
    @patch('app.routes.company_routes.get_db')
    @patch('app.routes.company_routes.enviar_email')
    def test_redefinir_senha(self, mock_enviar_email, mock_get_db):
        """Teste de redefinição de senha"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar uma empresa
        empresa = Company(
            name="Empresa Teste",
            address="Rua Teste, 123",
            phone="44444444444",
            cnpj="44444444444444",
            email="empresa@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        self.db.add(empresa)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição POST para redefinir senha
            response = client.post(
                "/api/empresa/redefinir_senha",
                data=json.dumps({"email": "empresa@teste.com"}),
                content_type="application/json"
            )
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertIn("E-mail de redefinição", response.json["mensagem"])
            
            # Verificar se o mock de enviar_email foi chamado
            mock_enviar_email.assert_called_once()
    
    @patch('app.routes.company_routes.get_db')
    def test_limpar_pendentes(self, mock_get_db):
        """Teste de limpeza de empresas pendentes expiradas"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar empresas pendentes, algumas expiradas e outras não
        now = datetime.utcnow()
        
        # Empresa pendente expirada (2 horas atrás)
        empresa_expirada = PendingCompany(
            name="Empresa Expirada",
            address="Rua Expirada, 123",
            phone="11111111111",
            cnpj="11111111111111",
            email="expirada@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        empresa_expirada.expiration = now - timedelta(hours=2)
        
        # Empresa pendente válida (ainda não expirou)
        empresa_valida = PendingCompany(
            name="Empresa Válida",
            address="Rua Válida, 456",
            phone="22222222222",
            cnpj="22222222222222",
            email="valida@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        empresa_valida.expiration = now + timedelta(hours=2)
        
        # Adicionar ao banco
        self.db.add(empresa_expirada)
        self.db.add(empresa_valida)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição DELETE para limpar pendentes
            response = client.delete("/api/empresa/limpar_pendentes")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            
            # Verificar que apenas a empresa expirada foi removida
            empresas_pendentes = self.db.query(PendingCompany).all()
            self.assertEqual(len(empresas_pendentes), 1)
            self.assertEqual(empresas_pendentes[0].email, "valida@teste.com")
    
    @patch('app.routes.company_routes.get_db')
    def test_obter_empresa(self, mock_get_db):
        """Teste para obter dados de uma empresa específica"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar uma empresa no banco
        empresa = Company(
            id="123e4567-e89b-12d3-a456-426614174000",  # UUID fixo para teste
            name="Empresa de Teste",
            address="Rua de Teste, 123",
            phone="33333333333",
            cnpj="33333333333333",
            email="empresa@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        
        self.db.add(empresa)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para obter empresa
            response = client.get(f"/api/empresa/obter/{empresa.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertEqual(data["id"], empresa.id)
            self.assertEqual(data["name"], "Empresa de Teste")
            self.assertEqual(data["email"], "empresa@teste.com")
    
    @patch('app.routes.company_routes.get_db')
    def test_find_by_substring(self, mock_get_db):
        """Teste para buscar empresas por substring no nome"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar várias empresas com nomes diferentes
        empresa1 = Company(
            name="Empresa ABC",
            address="Rua ABC, 123",
            phone="11111111111",
            cnpj="11111111111111",
            email="abc@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        
        empresa2 = Company(
            name="XYZ Corporation",
            address="Avenida XYZ, 456",
            phone="22222222222",
            cnpj="22222222222222",
            email="xyz@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        
        empresa3 = Company(
            name="ABC Comércio",
            address="Praça ABC, 789",
            phone="33333333333",
            cnpj="33333333333333",
            email="comercio@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        
        # Adicionar ao banco
        self.db.add_all([empresa1, empresa2, empresa3])
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para buscar por substring "ABC"
            response = client.get("/api/empresas/find_by_substring/ABC")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            empresas = response.json
            self.assertEqual(len(empresas), 2)  # Deve encontrar apenas as 2 com "ABC" no nome
            nomes = [e["name"] for e in empresas]
            self.assertIn("Empresa ABC", nomes)
            self.assertIn("ABC Comércio", nomes)
            self.assertNotIn("XYZ Corporation", nomes)
    
    @patch('app.routes.company_routes.get_db')
    def test_nova_senha(self, mock_get_db):
        """Teste para alterar a senha de uma empresa"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar uma empresa no banco com senha conhecida
        senha_original = "senha_original"
        hash_original = hashpw(senha_original.encode('utf-8'), gensalt()).decode('utf-8')
        
        empresa = Company(
            name="Empresa Teste",
            address="Rua Teste, 123",
            phone="44444444444",
            cnpj="44444444444444",
            email="empresa@teste.com",
            password_hash=hash_original
        )
        
        self.db.add(empresa)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Nova senha
            nova_senha = "senha_nova"
            
            # Fazer requisição PUT para alterar senha
            response = client.put(
                "/api/empresas/nova_senha",
                data=json.dumps({"email": "empresa@teste.com", "password": nova_senha}),
                content_type="application/json"
            )
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertIn("Senha alterada com sucesso", response.json["mensagem"])
            
            # Verificar se a senha foi alterada no banco
            empresa_atualizada = self.db.query(Company).filter_by(email="empresa@teste.com").first()
            
            self.assertTrue(
                checkpw(nova_senha.encode('utf-8'), empresa_atualizada.password_hash.encode('utf-8'))
            )
            
            self.assertFalse(
                checkpw(senha_original.encode('utf-8'), empresa_atualizada.password_hash.encode('utf-8'))
            )

if __name__ == "__main__":
    unittest.main()