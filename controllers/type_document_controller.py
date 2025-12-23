from flask import Blueprint,jsonify, request
from services.type_document_service import TypeDocumentService
from flask_jwt_extended import jwt_required

type_document_bp = Blueprint("type_document", __name__)

@type_document_bp.route("/create_type_document", methods=["POST"])
@jwt_required()

def create_type_document():
    data = request.json
    libelle = data.get("libelle")
    description = data.get("description")
    type_document = TypeDocumentService.creer_type_document(libelle,description)
    return jsonify({"message": "Le type document a été créer avec succes", "type_document": type_document.to_dict()}), 201

@type_document_bp.route("/get_type_document_by_id/<int:id>", methods=["GET"])
@jwt_required()

def get_type_document_by_id(id):
    type_document = TypeDocumentService.get_type_document_by_id(id)
    return jsonify({"message": "le type document par id", "type_document": type_document.to_dict()}), 200
    

@type_document_bp.route("/get_all_type_documents", methods=["GET"])
@jwt_required()

def get_all_type_documents():
    type_documents = TypeDocumentService.get_all_type_documents()
    return jsonify({"message": "La liste des types de document", "type_documents": [type_document.to_dict() for type_document in type_documents]}), 200
    

@type_document_bp.route("/update_type_document/<int:id>", methods=["PUT"])
@jwt_required()

def update_type_document(id):
    data = request.json
    libelle = data.get("libelle")
    description = data.get("description")
    type_document = TypeDocumentService.update_type_document(id,libelle,description)
    return jsonify({"message": "Le type de document a été modifier avec succes", "type_document": type_document.to_dict()}), 200
    

    
@type_document_bp.route("/delete_type_document/<int:id>", methods=["DELETE"])
@jwt_required()

def delete_type_document(id):
    TypeDocumentService.delete_type_document(id)
    return jsonify({"message": "Le type de document a été supprimer avec succes"}), 200


