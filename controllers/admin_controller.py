from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from services.utilisateur_service import UtilisateurService
from models.utilisateur import Utilisateur

admin_bp = Blueprint("admin", __name__)


def permission_required(permission_name):
    from functools import wraps
    from flask import jsonify
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if permission_name not in claims.get("permissions", []):
                return jsonify({"message": "Permission refusée"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@admin_bp.route("/utilisateur/<int:user_id>/toggle-activation", methods=["POST"])
@jwt_required() 
@permission_required("activer_utilisateur")
def toggle_user_activation(user_id):
    user = UtilisateurService.basculer_activation(user_id)
    if user:
        status = "activé" if user.is_active else "désactivé"
        return jsonify({
            "message": f"L'utilisateur {user.email} a été {status}.",
            "user": user.to_dict()
        }), 200
    return jsonify({
        "message": "Utilisateur introuvable"
    }), 404


@admin_bp.route("/utilisateur/<int:user_id>/desactiver", methods=["POST"])
@jwt_required()
@permission_required("desactiver_utilisateur")
def desactiver_utilisateur(user_id):
    user = UtilisateurService.desactiver(user_id)  # désactive toujours
    if user:
        return jsonify({
            "message": f"L'utilisateur {user.email} a été désactivé.",
            "user": user.to_dict()
        }), 200
    return jsonify({"message": "Utilisateur introuvable"}), 404