from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from config.database import db

class Lieu(db.Model):
    __tablename__ = "lieux"

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)         
    longitude = Column(Float)
    latitude = Column(Float)
    site_id = Column(Integer)
    
    verifications = relationship("Verification", back_populates="lieu")

    def to_dict(self):
        return{
            "id": self.id,
            "nom": self.nom,
            "longitude": self.longitude,
            "latitude":  self.latitude,
            "site_id":  self.site_id   
        }
