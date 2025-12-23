from models.type_document import TypeDocument
from config.database import db

class TypeDocumentService:
    @staticmethod
    def creer_type_document(libelle,description):
        type_document = TypeDocument(
            libelle = libelle,
            description = description
        )
        db.session.add(type_document)
        db.session.commit()
        return type_document


    @staticmethod
    def get_type_document_by_id(id):
        return TypeDocument.query.get(id)


    @staticmethod
    def get_all_type_documents():
        return TypeDocument.query.all()


    @staticmethod
    def update_type_document(id,libelle,description):
        type_document = TypeDocument.query.get(id)
        type_document.libelle = libelle
        type_document.description = description
        db.session.commit()
        return type_document

    @staticmethod
    def delete_type_document(id):
        type_document = TypeDocument.query.get(id)
        db.session.delete(type_document)
        db.session.commit()    



