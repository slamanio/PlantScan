from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class PlantSample(Base):
    __tablename__ = "plant_samples"

    id = Column(Integer, primary_key=True, index=True)
    image_filename = Column(String(255), nullable=False)
    caption   = Column(String(512), nullable=False)
    species   = Column(String(128))
    condition = Column(String(128))
