
from flask import Blueprint
from controllers.admin_controller import *

admin_bp = Blueprint("admin", __name__)

admin_bp.route("/utilisateur/<int:user_id>/toggle-activation", methods=["POST"])(
    toggle_user_activation
)

admin_bp.route("/utilisateur/<int:user_id>/desactiver", methods=["POST"])(
    desactiver_utilisateur
)

admin_bp.route("/utilisateurs/statistiques", methods=["GET"])(
    get_statistiques_utilisateurs
)
