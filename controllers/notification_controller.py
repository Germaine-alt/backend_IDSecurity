from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.notification_service import NotificationService

notification_bp = Blueprint("notifications", __name__)

@notification_bp.route("/mes-notifications", methods=["GET"])
@jwt_required()
def get_mes_notifications():
    user_id = get_jwt_identity()
    non_lues_seulement = request.args.get('non_lues', 'false').lower() == 'true'
    
    notifications = NotificationService.get_notifications_utilisateur(
        user_id, 
        non_lues_seulement=non_lues_seulement
    )
    
    return jsonify({
        "message": "Notifications récupérées",
        "notifications": [n.to_dict() for n in notifications]
    }), 200

@notification_bp.route("/count-non-lues", methods=["GET"])
@jwt_required()
def count_notifications_non_lues():
    user_id = get_jwt_identity()
    count = NotificationService.compter_notifications_non_lues(user_id)
    
    return jsonify({
        "count": count
    }), 200

@notification_bp.route("/<int:notification_id>/marquer-lu", methods=["PUT"])
@jwt_required()
def marquer_notification_lue(notification_id):
    user_id = get_jwt_identity()
    notification = NotificationService.marquer_comme_lu(notification_id, user_id)
    
    if not notification:
        return jsonify({"message": "Notification introuvable"}), 404
    
    return jsonify({
        "message": "Notification marquée comme lue",
        "notification": notification.to_dict()
    }), 200

@notification_bp.route("/marquer-toutes-lues", methods=["PUT"])
@jwt_required()
def marquer_toutes_lues():
    user_id = get_jwt_identity()
    NotificationService.marquer_toutes_comme_lues(user_id)
    
    return jsonify({
        "message": "Toutes les notifications ont été marquées comme lues"
    }), 200

@notification_bp.route("/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def supprimer_notification(notification_id):
    user_id = get_jwt_identity()
    success = NotificationService.supprimer_notification(notification_id, user_id)
    
    if not success:
        return jsonify({"message": "Notification introuvable"}), 404
    
    return jsonify({
        "message": "Notification supprimée"
    }), 200