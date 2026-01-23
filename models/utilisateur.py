from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.database import db
from models.notification import Notification

class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    prenom = Column(String(255))
    email = Column[str](String(255), unique=True)
    telephone = Column(String(50))
    mot_passe = Column(String(255))
    poste = Column(String(255))
    is_active = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="utilisateurs")
    verifications = relationship("Verification", back_populates="utilisateur")
    ocr_results = relationship("OCRResult", back_populates="utilisateur")
    notifications = relationship("Notification", foreign_keys="Notification.utilisateur_id", back_populates="utilisateur")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "email": self.email,
            "telephone": self.telephone,
            "poste": self.poste,
            "is_active": self.is_active,
            "role_id": self.role_id,

            # Correction role
            "role": {
                "id": self.role.id,
                "libelle": self.role.libelle,
                "permissions": self.role.permissions
            } if self.role else None
        }
