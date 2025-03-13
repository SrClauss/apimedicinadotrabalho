import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app import create_app, drop_test_db
from app.database import Base
from app.models.exam import Exam
from app.models.user import User
from app.models.company import Company
from app import TestSession
from bcrypt import hashpw, gensalt

class ExamRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Limpar o banco de dados de teste
        drop_test_db()
        
        # Configurar o banco de dados de teste
        self.db = TestSession()
        Base.metadata.create_all(bind=self.db.bind)
        
        # Criar um usuário e uma empresa para os testes
        self.test_user = User(
            name="Usuário Teste",
            address="Rua Teste, 123",
            phone="12345678901",
            cpf="12345678901",
            email="usuario@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8'),
            role=0
        )
        
        self.test_company = Company(
            name="Empresa Teste",
            address="Rua Empresa, 456",
            phone="98765432109",
            cnpj="12345678901234",
            email="empresa@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        
        self.db.add(self.test_user)
        self.db.add(self.test_company)
        self.db.commit()
        
    def tearDown(self):
        """Limpeza executada após cada teste"""
        self.db.close()
        drop_test_db()
    
    @patch('app.routes.exam_routes.get_db')
    def test_criar_exame(self, mock_get_db):
        """Teste de criação de exame"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Dados para criação do exame
            dados_exame = {
                "user_id": str(self.test_user.id),
                "company_id": str(self.test_company.id),
                "title": "Hemograma Completo",
                "description": "Exame para análise de sangue"
            }
            
            # Fazer requisição POST para criar exame
            response = client.post(
                "/api/exames/criar",
                data=json.dumps(dados_exame),
                content_type="application/json"
            )
            
            # Verificações
            self.assertEqual(response.status_code, 201)
            self.assertIn("id", response.json)
            
            # Verificar se o exame foi criado no banco
            exame = self.db.query(Exam).filter_by(
                user_id=self.test_user.id,
                company_id=self.test_company.id
            ).first()
            
            self.assertIsNotNone(exame)
            self.assertEqual(exame.title, "Hemograma Completo")
    
    @patch('app.routes.exam_routes.get_db')
    def test_obter_exame(self, mock_get_db):
        """Teste para obter um exame específico"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar um exame
        exame = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Radiografia",
            description="Exame de imagem do tórax"
        )
        self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para obter o exame
            response = client.get(f"/api/exames/obter/{exame.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["id"], str(exame.id))
            self.assertEqual(response.json["title"], "Radiografia")
    
    @patch('app.routes.exam_routes.get_db')
    def test_atualizar_exame(self, mock_get_db):
        """Teste para atualizar um exame"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar um exame
        exame = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Ultrassom",
            description="Exame pendente"
        )
        self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Dados atualizados
            dados_atualizados = {
                "title": "Ultrassom Abdominal",
                "description": "Exame finalizado: sem anormalidades"
            }
            
            # Fazer requisição PUT para atualizar o exame
            response = client.put(
                f"/api/exames/atualizar/{exame.id}",
                data=json.dumps(dados_atualizados),
                content_type="application/json"
            )
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertIn("Exame atualizado", response.json["mensagem"])
            
            # Verificar se os dados foram atualizados no banco
            exame_atualizado = self.db.query(Exam).get(exame.id)
            self.assertEqual(exame_atualizado.title, "Ultrassom Abdominal")
            self.assertEqual(exame_atualizado.description, "Exame finalizado: sem anormalidades")
    
    @patch('app.routes.exam_routes.get_db')
    def test_deletar_exame(self, mock_get_db):
        """Teste para deletar um exame"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar um exame
        exame = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Ressonância",
            description="Exame de cabeça"
        )
        self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição DELETE para excluir o exame
            response = client.delete(f"/api/exames/deletar/{exame.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            self.assertIn("Exame excluído", response.json["mensagem"])
            
            # Verificar que o exame foi excluído do banco
            exame_deletado = self.db.query(Exam).get(exame.id)
            self.assertIsNone(exame_deletado)
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_exames(self, mock_get_db):
        """Teste para listar todos os exames"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Adicionar alguns exames
        for i in range(3):
            exame = Exam(
                user_id=self.test_user.id,
                company_id=self.test_company.id,
                title=f"Exame {i+1}",
                description=f"Descrição do exame {i+1}"
            )
            self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames
            response = client.get("/api/exames/listar")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            exames = response.json
            self.assertEqual(len(exames), 3)
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_por_usuario(self, mock_get_db):
        """Teste para listar exames por usuário"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar outro usuário
        outro_usuario = User(
            name="Outro Usuário",
            address="Outra Rua, 789",
            phone="00000000000",
            cpf="00000000000",
            email="outro@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8'),
            role=0
        )
        self.db.add(outro_usuario)
        self.db.commit()
        
        # Adicionar exames para diferentes usuários
        exame1 = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Exame Usuário 1",
            description="Descrição exame usuário 1"
        )
        
        exame2 = Exam(
            user_id=outro_usuario.id,
            company_id=self.test_company.id,
            title="Exame Usuário 2",
            description="Descrição exame usuário 2"
        )
        
        self.db.add(exame1)
        self.db.add(exame2)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames por usuário
            response = client.get(f"/api/exames/listar_por_usuario/{self.test_user.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            exames = response.json
            self.assertEqual(len(exames), 1)
            self.assertEqual(exames[0]["title"], "Exame Usuário 1")
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_por_empresa(self, mock_get_db):
        """Teste para listar exames por empresa"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar outra empresa
        outra_empresa = Company(
            name="Outra Empresa",
            address="Outra Avenida, 999",
            phone="99999999999",
            cnpj="98765432109876",
            email="outra@empresa.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8')
        )
        self.db.add(outra_empresa)
        self.db.commit()
        
        # Adicionar exames para diferentes empresas
        exame1 = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Exame Empresa 1",
            description="Descrição exame empresa 1"
        )
        
        exame2 = Exam(
            user_id=self.test_user.id,
            company_id=outra_empresa.id,
            title="Exame Empresa 2",
            description="Descrição exame empresa 2"
        )
        
        self.db.add(exame1)
        self.db.add(exame2)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames por empresa
            response = client.get(f"/api/exames/listar_por_empresa/{self.test_company.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
            exames = response.json
            self.assertEqual(len(exames), 1)
            self.assertEqual(exames[0]["title"], "Exame Empresa 1")
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_por_data(self, mock_get_db):
        """Teste para listar exames por data"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Data para teste (hoje)
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Adicionar exames
        exame = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Exame Hoje",
            description="Descrição exame hoje"
        )
        self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames por data
            response = client.get(f"/api/exames/listar_por_data/{hoje}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_por_data_usuario(self, mock_get_db):
        """Teste para listar exames por data e usuário"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Criar outro usuário
        outro_usuario = User(
            name="Outro Usuário",
            address="Outra Rua, 789",
            phone="00000000000",
            cpf="00000000000",
            email="outro@teste.com",
            password_hash=hashpw("senha123".encode('utf-8'), gensalt()).decode('utf-8'),
            role=0
        )
        self.db.add(outro_usuario)
        self.db.commit()
        
        # Data para teste (hoje)
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Adicionar exames para diferentes usuários
        exame1 = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Exame Usuário 1",
            description="Descrição exame usuário 1"
        )
        
        exame2 = Exam(
            user_id=outro_usuario.id,
            company_id=self.test_company.id,
            title="Exame Usuário 2",
            description="Descrição exame usuário 2"
        )
        
        self.db.add(exame1)
        self.db.add(exame2)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames por data e usuário
            response = client.get(f"/api/exames/listar_por_data_usuario/{hoje}/{self.test_user.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)
    
    @patch('app.routes.exam_routes.get_db')
    def test_listar_por_data_empresa(self, mock_get_db):
        """Teste para listar exames por data e empresa"""
        # Configurar o mock para retornar o banco de dados de teste
        mock_get_db.return_value = self.db
        
        # Data para teste (hoje)
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Adicionar exame
        exame = Exam(
            user_id=self.test_user.id,
            company_id=self.test_company.id,
            title="Exame Empresa 1",
            description="Descrição exame empresa 1"
        )
        
        self.db.add(exame)
        self.db.commit()
        
        # Criar a aplicação de teste
        self.app = create_app(testing=True)
        
        with self.app.test_client() as client:
            # Fazer requisição GET para listar exames por data e empresa
            response = client.get(f"/api/exames/listar_por_data_empresa/{hoje}/{self.test_company.id}")
            
            # Verificações
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()