from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.database import db
from sqlalchemy.dialects.mysql import JSON


class Role(db.Model):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(255), nullable=False)     
    permissions = Column(JSON)
    utilisateurs = relationship("Utilisateur", back_populates="role")

    def to_dict(self):
            return {
                "id": self.id,
                "libelle": self.libelle,
                "permissions": self.permissions
            }
