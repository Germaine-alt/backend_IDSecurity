from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from config.database import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    titre = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    est_lu = Column(Boolean, default=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    utilisateur = relationship("Utilisateur", foreign_keys=[utilisateur_id])
    
    utilisateur_concerne_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    utilisateur_concerne = relationship("Utilisateur", foreign_keys=[utilisateur_concerne_id])

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "message": self.message,
            "type": self.type,
            "est_lu": self.est_lu,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "utilisateur_id": self.utilisateur_id,
            "utilisateur_concerne": {
                "id": self.utilisateur_concerne.id,
                "nom": self.utilisateur_concerne.nom,
                "prenom": self.utilisateur_concerne.prenom,
                "email": self.utilisateur_concerne.email
            } if self.utilisateur_concerne else None
        }