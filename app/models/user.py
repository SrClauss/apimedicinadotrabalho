# app/models/user.py
from sqlalchemy import Boolean, Column, String, DateTime, func, Integer
from sqlalchemy.orm import relationship, declarative_base
from bcrypt import hashpw, gensalt, checkpw
from flask import current_app
import jwt
from datetime import datetime, timedelta
import pytz
import ulid
from app.database import Base

# Define o fuso horário padrão
timezone = pytz.timezone("UTC")


# Constantes para os roles
class UserRole:
    ADMIN = 0
    EDITOR = 1
    WORKER = 3

    @classmethod
    def get_choices(cls):
        return [(cls.ADMIN, "Admin"), (cls.EDITOR, "Editor"), (cls.WORKER, "Worker")]

    @classmethod
    def get_label(cls, value):
        for val, label in cls.get_choices():
            if val == value:
                return label
        return "Desconhecido"

class User(Base):
    __tablename__ = "users"
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))
    name = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    address = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    cpf = Column(String(14), unique=True, nullable=True)
    role = Column(Integer, default=UserRole.WORKER, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Use string para evitar importação circular
    exams = relationship("Exam", back_populates="user")

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}', cpf='{self.cpf}', role='{UserRole.get_label(self.role)}')>"

    def check_password(self, password):
        return checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def get_role_label(self):
        return UserRole.get_label(self.role)
    
    
    def to_dto(self):
        return UserDTO(
            email=self.email,
            name=self.name,
            address=self.address,
            phone=self.phone,
            cpf=self.cpf,
        )
        
        


class PendingUser(Base):
    __tablename__ = "pending_users"
    id = Column(String, primary_key=True, default=lambda: str(ulid.new()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    address = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    cpf = Column(String(14), unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    expiration = Column(
        DateTime, default=lambda: datetime.now(timezone) + timedelta(hours=1)
    )  # Expira em 1 hora

    def to_jwt(self):
        payload = {
            "email": self.email,
            "exp": self.expiration,  # Usa o tempo de expiração do pending_user
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


class UserDTO:
    def __init__(
        self, email, name=None, password=None, address=None, phone=None, cpf=None
    ):
        self.email = email
        self.name = name
        self.password = password
        self.address = address
        self.phone = phone
        self.cpf = cpf

    def to_dict(self):
        return {
            "email": self.email,
            "name": self.name,
            "password": self.password,
            "address": self.address,
            "phone": self.phone,
            "cpf": self.cpf,
        }

    @staticmethod
    def from_dict(data):
        return UserDTO(
            email=data["email"],
            name=data["name"],
            password=data.get("password"),
            address=data.get("address"),
            phone=data.get("phone"),
            cpf=data.get("cpf"),
        )

    @staticmethod
    def from_jwt(token):
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"require_exp": True},  # Exige validação de expiração
            )
            return UserDTO(
                name=data["name"],
                email=data["email"],
                address=data.get("address"),
                phone=data.get("phone"),
                cpf=data.get("cpf"),
            )
        except jwt.ExpiredSignatureError:
            return None  # Token expirado
        except Exception as e:
            current_app.logger.error(f"Erro ao decodificar token: {str(e)}")
            return None

    def to_jwt(self):
        payload = {
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "phone": self.phone,
            "cpf": self.cpf,
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
