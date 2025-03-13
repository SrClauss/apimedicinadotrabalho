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

