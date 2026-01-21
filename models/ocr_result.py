from datetime import datetime
from sqlalchemy import Column, DateTime,Integer,ForeignKey
from sqlalchemy.orm import relationship
from config.database import db
from sqlalchemy.sql import func





class OCRResult(db.Model):
    __tablename__ = "ocr_results"

    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255))
    text_detected = db.Column(db.Text)
    confidence = db.Column(db.Float)
    bbox = db.Column(db.Text)
    annotated_image = db.Column(db.String(255))
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'))
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    nom_externe = db.Column(db.String(100), nullable=True)
    prenom_externe = db.Column(db.String(100), nullable=True)

    document = relationship("Document", back_populates="ocr_results")
    utilisateur = relationship("Utilisateur", back_populates="ocr_results")
    verifications = relationship("Verification", back_populates="ocr_results")

    def to_dict(self):
        return {
            'id': self.id,
            'image_name': self.image_name,
            'text_detected': self.text_detected,
            'confidence': self.confidence,
            'bbox': self.bbox,
            'annotated_image': self.annotated_image,
            'utilisateur_id': self.utilisateur_id,
            'document_id': self.document_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            "nom_externe": self.nom_externe,
            "prenom_externe": self.prenom_externe,
            'utilisateur': {
                'id': self.utilisateur.id,
                'nom': self.utilisateur.nom,
                'prenom': self.utilisateur.prenom,
                'email': self.utilisateur.email
            } if self.utilisateur else None,
            'document': {
                'id': self.document.id,
                'numero_document': self.document.numero_document,
                'nom': self.document.nom,
                'prenom': self.document.prenom,
                'type_document': self.document.type_document.libelle 
                                if self.document.type_document else None
            } if self.document else None

        }