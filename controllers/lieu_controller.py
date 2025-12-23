from flask import Blueprint, jsonify, request 
from services.lieu_service import LieuService
from flask_jwt_extended import jwt_required

lieu_bp = Blueprint("lieu", __name__)

@lieu_bp.route("/create_lieu", methods=["POST"])
@jwt_required()

def create_lieu():
    data = request.json
    nom = data.get("nom")
    longitude = data.get("longitude")
    latitude = data.get("latitude")
    lieu = LieuService.creer_lieu(nom,longitude,latitude)
    return jsonify({"message": "Le lieu a été créer avec succes", "lieu": lieu.to_dict()}), 201

@lieu_bp.route("/get_lieu_by_id/<int:id>", methods=["GET"])
@jwt_required()

def get_lieu_by_id(id):
    lieu = LieuService.get_lieu_by_id(id)
    return jsonify({"message":"lieu par id", "lieu": lieu.to_dict()}), 200


@lieu_bp.route("/get_all_lieux", methods=["GET"])
@jwt_required()

def get_all_lieux():
    lieux = LieuService.get_all_lieux()
    return jsonify({"message": "La liste des lieux","lieux":[lieu.to_dict() for lieu in lieux]}), 200


@lieu_bp.route("/update_lieu/<int:id>", methods=["PUT"])
@jwt_required()

def update_lieu(id):
    data = request.json
    nom = data.get("nom")
    longitude = data.get("longitude")
    latitude = data.get("latitude")
    lieu = LieuService.update_lieu(id,nom,longitude,latitude)
    return jsonify({"message": "Le lieu a été modifier avec succes", "lieu": lieu.to_dict()}), 200


@lieu_bp.route("/delete_lieu/<int:id>", methods=["DELETE"])
@jwt_required()

def delete_lieu(id):
    LieuService.delete_lieu(id)
    return jsonify({"message": "Le lieu a été supprimer avec succes"}), 200


