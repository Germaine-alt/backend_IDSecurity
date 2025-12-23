from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.database import db


class TypeDocument(db.Model):
    __tablename__ = "type_documents"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(255), nullable=False)      
    description = Column(String(255))

    documents = relationship("Document", back_populates="type_document")


    def to_dict(self):
        return{
            "id": self.id,
            "libelle": self.libelle,
            "description": self.description
        }

