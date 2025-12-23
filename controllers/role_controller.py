
from flask import Blueprint,jsonify, request
from services.role_service import RoleService
from flask_jwt_extended import jwt_required

role_bp = Blueprint("role", __name__)

@role_bp.route("/create_role", methods=["POST"])
@jwt_required()

def create_role():
    data = request.json
    libelle = data.get("libelle")
    permissions = data.get("permissions")
    role = RoleService.creer_role(libelle, permissions)
    return jsonify({"message": "Le role a été créer avec succes", "role": role.to_dict()}), 201

@role_bp.route("/get_role_by_id/<int:id>", methods=["GET"])
@jwt_required()
def get_role_by_id(id):
    role = RoleService.get_role_by_id(id)
    return jsonify({"message": "role par id", "role": role.to_dict()}), 200
    

@role_bp.route("/get_all_roles", methods=["GET"])
@jwt_required()

def get_all_roles():
    roles = RoleService.get_all_roles()
    return jsonify({"message": "La liste des rôles", "roles": [role.to_dict() for role in roles]}), 200
    

@role_bp.route("/update_role/<int:id>", methods=["PUT"])
@jwt_required()

def update_role(id):
    data = request.json
    libelle = data.get("libelle")
    permissions = data.get("permissions")
    role = RoleService.update_role(id,libelle,permissions)
    return jsonify({"message": "Le rôle a été modifier avec succes", "role": role.to_dict()}), 200
    

    
@role_bp.route("/delete_role/<int:id>", methods=["DELETE"])
@jwt_required()

def delete_role(id):
    RoleService.delete_role(id)
    return jsonify({"message": "Le rôle a été supprimer avec succes"}), 200



