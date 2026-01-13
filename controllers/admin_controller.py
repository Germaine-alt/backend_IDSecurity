from services.utilisateur_service import UtilisateurService
from flask_jwt_extended import jwt_required, get_jwt
from models.utilisateur import Utilisateur
from flask import jsonify


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


@jwt_required()
@permission_required("desactiver_utilisateur")
def desactiver_utilisateur(user_id):
    user = UtilisateurService.desactiver(user_id)  
    if user:
        return jsonify({
            "message": f"L'utilisateur {user.email} a été désactivé.",
            "user": user.to_dict()
        }), 200
    return jsonify({"message": "Utilisateur introuvable"}), 404



@jwt_required()
@permission_required("activer_utilisateur")
def get_statistiques_utilisateurs():
    """Endpoint pour récupérer les statistiques des utilisateurs"""
    stats = UtilisateurService.get_statistiques_utilisateurs()
    return jsonify({
        "message": "Statistiques récupérées avec succès",
        "data": stats
    }), 200