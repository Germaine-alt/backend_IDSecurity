from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.verification_service import VerificationService

verification_bp = Blueprint('verification_bp', __name__)

@verification_bp.route('/get_all_verifications', methods=['GET'])
@jwt_required()
def get_all_verifications():
    verifications = VerificationService.get_all_verifications()
    return jsonify({"message": "La liste des verifications", "verifications": [verification.to_dict() for verification in verifications]}), 200
    

@verification_bp.route('/get_verification_by_id/<int:id>', methods=['GET'])
@jwt_required()
def get_verification_by_id(id):
    verification = VerificationService.get_verification_by_id(id)
    return jsonify({"message": "La verification par id", "verification": verification.to_dict()}), 200



@verification_bp.route('/mes_verifications', methods=['GET'])
@jwt_required()
def get_mes_verifications():
    try:
        verifications = VerificationService.get_user_verifications()
        if not verifications:
            return jsonify({
                "message": "Aucune vérification trouvée",
                "verification": []
            }),200
        return jsonify({
            "message": "Liste des verifications de l'utilisateur",
            "verifications": [verification.to_dict() for verification in verifications],
            "total": len(verifications)
        }),200
    except Exception as e:        
        return jsonify({            
            "message": f"Erreur lors de la recuperation des verifications: {str(e)}"        
    }), 500      




@verification_bp.route("/count_verifications", methods=["GET"])
@jwt_required()
def count_verifications():
    total = VerificationService.count_verifications()
    return jsonify({
        "message" : "Nombre total de verification",
        "total" : total
    }),200

