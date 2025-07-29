from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    plants = relationship("Plant", back_populates="owner")

class Plant(Base):
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1500), nullable=False)
    species = Column(String(1500), nullable=False)
    description = Column(String(1500), nullable=True)
    count = Column(Integer, default=0)
    images = relationship("PlantImage", back_populates="plant", cascade="all, delete")

    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    owner = relationship("User", back_populates="plants")

class PlantImage(Base):
    __tablename__ = 'plant_images'
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id'))

    plant = relationship("Plant", back_populates="images")