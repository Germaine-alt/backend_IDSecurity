from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.utilisateur_service import UtilisateurService
from flask import jsonify, request
import re


@jwt_required()
def register():
    data = request.json
    user = UtilisateurService.creer_utilisateur(
        nom=data["nom"],
        prenom=data["prenom"],
        email=data["email"],
        poste=data["poste"],
        telephone=data["telephone"],
        role_id=data["role_id"]
    )
    return jsonify({
        "message": "Utilisateur créé avec succès",
        "user": user.to_dict()
    }), 201



def login():
    data = request.get_json()
    email = data.get("email")
    mot_passe = data.get("mot_passe")

    
    user = UtilisateurService.verifier_connexion(email=email, mot_passe=mot_passe)

    if not user:
        return jsonify({"message": "Identifiants incorrects"}), 401

    
    access_token = create_access_token(
        identity=str(user.id),  
        additional_claims={
            "permissions": user.role.permissions if user.role else [],
            "role": user.role.libelle if user.role else None
        }
    )

    
    return jsonify({
        "message": "Connexion réussie",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "telephone": user.telephone,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
            "poste": user.poste,
            "role": {
                    "id": user.role.id,
                    "libelle": user.role.libelle,
                    "permissions": user.role.permissions
            } if user.role else None        
        }
    }), 200


@jwt_required()
def get_all_utilisateurs():
    users = UtilisateurService.get_all_utilisateurs()
    return jsonify({"message": "Liste des utilisateurs", "users": [u.to_dict() for u in users]}), 200


@jwt_required()
def get_current_user():
    
    user_id = get_jwt_identity()

    
    user = UtilisateurService.get_user(user_id)

    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    
    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "telephone": user.telephone,
        "poste": user.poste,
        "is_active": user.is_active,
        "role_id": user.role_id
    }), 200


@jwt_required()
def update_utilisateur(id):
    data = request.json
    user = UtilisateurService.update_utilisateur(
        id,
        nom=data.get("nom"),
        prenom=data.get("prenom"),
        email=data.get("email"),
        telephone=data.get("telephone"),
        mot_passe=data.get("mot_passe"),
        poste=data.get("poste"),
        role_id=data.get("role_id")
    )
    if not user:
        return jsonify({"message": "Utilisateur introuvable"}), 404
    return jsonify({"message": "Utilisateur modifié avec succès", "user": user.to_dict()}), 200


@jwt_required()
def changer_mot_de_passe():
    """Endpoint pour changer le mot de passe"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    
    required_fields = ["ancien_mot_passe", "nouveau_mot_passe", "confirmation_mot_passe"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"message": f"Le champ {field} est requis"}), 400
    
    ancien_mot_passe = data["ancien_mot_passe"]
    nouveau_mot_passe = data["nouveau_mot_passe"]
    confirmation_mot_passe = data["confirmation_mot_passe"]
    
    
    if nouveau_mot_passe != confirmation_mot_passe:
        return jsonify({"message": "Les mots de passe ne correspondent pas"}), 400
    
    
    if len(nouveau_mot_passe) < 8:
        return jsonify({"message": "Le mot de passe doit contenir au moins 8 caractères"}), 400
    
    
    if not re.search(r"[A-Z]", nouveau_mot_passe):
        return jsonify({"message": "Le mot de passe doit contenir au moins une lettre majuscule"}), 400
    if not re.search(r"[a-z]", nouveau_mot_passe):
        return jsonify({"message": "Le mot de passe doit contenir au moins une lettre minuscule"}), 400
    if not re.search(r"[0-9]", nouveau_mot_passe):
        return jsonify({"message": "Le mot de passe doit contenir au moins un chiffre"}), 400
    
    
    user, error = UtilisateurService.changer_mot_de_passe(
        user_id, 
        ancien_mot_passe, 
        nouveau_mot_passe
    )
    
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify({
        "message": "Mot de passe modifié avec succès",
        "user": user.to_dict()
    }), 200

@jwt_required()
def reinitialiser_mot_de_passe(user_id):
    
    current_user_id = get_jwt_identity()
    current_user = UtilisateurService.get_user(current_user_id)
    
    
    if not current_user.role or current_user.role.libelle != "admin":
        return jsonify({"message": "Permission refusée"}), 403
    
    
    mot_passe_temp, error = UtilisateurService.reinitialiser_mot_de_passe(user_id)
    
    if error:
        return jsonify({"message": error}), 400
    
    return jsonify({
        "message": "Mot de passe réinitialisé avec succès",
        "mot_passe_temporaire": mot_passe_temp
    }), 200