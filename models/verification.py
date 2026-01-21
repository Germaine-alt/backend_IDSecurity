from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.database import db
from sqlalchemy.sql import func


class Verification(db.Model):
    __tablename__ = 'verifications'

    id = Column(Integer, primary_key=True)
    # date_verification = Column(DateTime, default=datetime.utcnow)
    date_verification = Column(DateTime(timezone=True), server_default=func.now())

    resultat_photo = Column(String(50))   
    resultat_donnee = Column(String(50))  
    url_image_echec = Column(String(255), nullable=True)

    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    lieu_id = Column(Integer, ForeignKey('lieux.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    ocr_result_id = Column(Integer, ForeignKey('ocr_results.id'), nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="verifications")
    lieu = relationship("Lieu", back_populates="verifications")
    document = relationship("Document", back_populates="verifications")
    ocr_results = relationship("OCRResult", back_populates="verifications")

    def to_dict(self):
        return {
            "id": self.id,
            "date_verification": self.date_verification.isoformat(),
            "resultat_photo": self.resultat_photo,
            "resultat_donnee": self.resultat_donnee,
            "url_image_echec": self.url_image_echec,

            "nom_externe": self.ocr_results.nom_externe if self.ocr_results else None,
            "prenom_externe": self.ocr_results.prenom_externe if self.ocr_results else None,

            "utilisateur": {
                "id": self.utilisateur.id,
                "nom": self.utilisateur.nom,
                "prenom": self.utilisateur.prenom,
                "email": self.utilisateur.email,

            } if self.utilisateur else None,
            "lieu": {
                "id": self.lieu.id,
                "nom": self.lieu.nom,
                "longitude": self.lieu.longitude,
                "latitude": self.lieu.latitude,
                "site_id": self.lieu.site_id

            } if self.lieu else None,
            "document": {
                "id": self.document.id,
                "numero_document": self.document.numero_document
            } if self.document else None,
            "ocr_result_id": self.ocr_result_id
        }
