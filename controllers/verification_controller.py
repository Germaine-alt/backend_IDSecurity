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

