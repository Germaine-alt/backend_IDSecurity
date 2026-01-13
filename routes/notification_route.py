from flask import Blueprint
from controllers.notification_controller import *

notification_bp = Blueprint("notifications", __name__)

notification_bp.route("/mes-notifications", methods=["GET"])(
    get_mes_notifications
)

notification_bp.route("/count-non-lues", methods=["GET"])(
    count_notifications_non_lues
)

notification_bp.route("/<int:notification_id>/marquer-lu", methods=["PUT"])(
    marquer_notification_lue
)

notification_bp.route("/marquer-toutes-lues", methods=["PUT"])(
    marquer_toutes_lues
)

notification_bp.route("/<int:notification_id>", methods=["DELETE"])(
    supprimer_notification
)
