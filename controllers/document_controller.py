from flask import Blueprint,jsonify, request
from services.document_service import DocumentService
from flask_jwt_extended import jwt_required

document_bp = Blueprint("document", __name__)

@document_bp.route("/create_document", methods=["POST"])
@jwt_required()

def create_document():
    data = request.json
    numero_document = data.get("numero_document")
    nom = data.get("nom")
    prenom = data.get("prenom")
    nationalite = data.get("nationalite")
    date_de_naissance = data.get("date_de_naissance")
    sexe = data.get("sexe")
    lieu_naissance = data.get("lieu_naissance")
    date_de_delivrance = data.get("date_de_delivrance")
    date_d_expiration = data.get("date_d_expiration")
    chemin_image = data.get("chemin_image")
    taille = data.get("taille")
    poids = data.get("poids")
    profession = data.get("profession")
    domicile = data.get("domicile")
    organisme_delivrance = data.get("organisme_delivrance")
    info_nfc = data.get("info_nfc")
    type_document_id = data.get("type_document_id")
    document = DocumentService.creer_document(numero_document,nom,prenom,nationalite,date_de_naissance,sexe,lieu_naissance,date_de_delivrance,date_d_expiration,chemin_image,taille,poids,profession,domicile,organisme_delivrance,info_nfc,type_document_id)
    return jsonify({"message": "Le document a été créer avec succes", "document": document.to_dict()}), 201

@document_bp.route("/get_document_by_id/<int:id>", methods=["GET"])
@jwt_required()

def get_document_by_id(id):
    document = DocumentService.get_document_by_id(id)
    return jsonify({"message": "Le document par id", "document": document.to_dict()}), 200
    

@document_bp.route("/get_all_documents", methods=["GET"])
@jwt_required()

def get_all_documents():
    documents = DocumentService.get_all_documents()
    return jsonify({"message": "La liste des documents", "documents": [document.to_dict() for document in documents]}), 200
    

@document_bp.route("/update_document/<int:id>", methods=["PUT"])
@jwt_required()

def update_document(id):
    data = request.json
    numero_document = data.get("numero_document")
    nom = data.get("nom")
    prenom = data.get("prenom")
    nationalite = data.get("nationalite")
    date_de_naissance = data.get("date_de_naissance")
    sexe = data.get("sexe")
    lieu_naissance = data.get("lieu_naissance")
    date_de_delivrance = data.get("date_de_delivrance")
    date_d_expiration = data.get("date_d_expiration")
    chemin_image = data.get("chemin_image")
    taille = data.get("taille")
    poids = data.get("poids")
    profession = data.get("profession")
    domicile = data.get("domicile")
    organisme_delivrance = data.get("organisme_delivrance")
    info_nfc = data.get("info_nfc")
    type_document_id = data.get("type_document_id")    
    document = DocumentService.update_document(id,numero_document,nom,prenom,nationalite,date_de_naissance,sexe,lieu_naissance,date_de_delivrance,date_d_expiration,chemin_image,taille,poids,profession,domicile,organisme_delivrance,info_nfc,type_document_id)
    return jsonify({"message": "Le document a été modifier avec succes", "document": document.to_dict()}), 200
    

    
@document_bp.route("/delete_document/<int:id>", methods=["DELETE"])
@jwt_required()

def delete_document(id):
    DocumentService.delete_document(id)
    return jsonify({"message": "Le document a été supprimer avec succes"}), 200