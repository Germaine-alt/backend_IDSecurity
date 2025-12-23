from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from config.database import db


class Document(db.Model):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    numero_document = Column(String(255))
    nom = Column(String(255))
    prenom = Column(String(255))
    nationalite = Column(String(255))
    date_de_naissance = Column(Date)
    sexe = Column(String(10))
    lieu_naissance = Column(String(255))
    date_de_delivrance = Column(Date)
    date_d_expiration = Column(Date)
    chemin_image = Column(Text)
    taille = Column(Float)
    poids = Column(Float)
    profession = Column(String(255))
    domicile = Column(String(255))
    organisme_delivrance = Column(String(255))
    info_nfc = Column(String(255))
    type_document_id = Column(Integer, ForeignKey("type_documents.id"))


    type_document = relationship("TypeDocument", back_populates="documents")
    verifications = relationship("Verification", back_populates="document")
    ocr_results = relationship("OCRResult", back_populates="document")



    def to_dict(self):      
        return {
            "id": self.id,
            "numero_document": self.numero_document,
            "nom": self.nom,
            "prenom": self.prenom,
            "nationalite": self.nationalite,
            "date_de_naissance": self.date_de_naissance.isoformat() if self.date_de_naissance else None,
            "sexe": self.sexe,
            "lieu_naissance": self.lieu_naissance,
            "date_de_delivrance": self.date_de_delivrance.isoformat() if self.date_de_delivrance else None,
            "date_d_expiration": self.date_d_expiration.isoformat() if self.date_d_expiration else None,
            "chemin_image": self.chemin_image,  
            "taille": self.taille,
            "poids": self.poids,
            "profession": self.profession,
            "domicile": self.domicile,
            "organisme_delivrance": self.organisme_delivrance,
            "info_nfc": self.info_nfc,
            "type_document_id": self.type_document_id,
            "type_document": {
                "id": self.type_document.id,
                "libelle": self.type_document.libelle,
                "description": self.type_document.description
            } if self.type_document else None
        }