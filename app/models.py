from sqlalchemy import Column, Integer, String, ForeignKey
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
    description = Column(String(1500), nullable=True)
    image_path = Column(String(255), nullable=False)
    image_hash = Column(String(255), unique=True, nullable=False)
    color = Column(String(255), nullable=False)

    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    plant = relationship("Plant", back_populates="images")
    user = relationship("User", back_populates="plant_images")
    infos = relationship("PlantInfos", back_populates="plant_image", cascade="all, delete")

class PlantInfos(Base):
    __tablename__ = 'plant_infos'

    id = Column(Integer, primary_key=True, index=True)
    condition= Column(String(2000), nullable=False)
    solution = Column(String(2000), nullable=False)
    image_path = Column(String(2000), nullable=False)
    color = Column(String(255), nullable=False)
    # Relacionamento direto com PlantImage
    plant_image_id = Column(Integer, ForeignKey("plant_images.id", ondelete="CASCADE"), nullable=False)
    plant_image = relationship("PlantImage", back_populates="infos")
