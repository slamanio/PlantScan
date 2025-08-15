from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image = Column(String(255), nullable=True)
    theme = Column(String(255), nullable=True)

    plant_images = relationship("PlantImage", back_populates="user", passive_deletes=True)


class Plant(Base):
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1500), nullable=False)
    species = Column(String(1500), nullable=False)
    count = Column(Integer, default=0)

    images = relationship("PlantImage", back_populates="plant", cascade="all, delete")


class PlantImage(Base):
    __tablename__ = 'plant_images'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1500), nullable=False)
    description = Column(JSON, nullable=True)
    image_path = Column(JSON, nullable=False)
    color = Column(JSON, nullable=False)

    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    plant = relationship("Plant", back_populates="images")
    user = relationship("User", back_populates="plant_images")

