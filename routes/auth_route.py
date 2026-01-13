from flask import Blueprint
from controllers.auth_controller import *

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/register", methods=["POST"])(
    register
)

auth_bp.route("/login", methods=["POST"])(
    login
)

auth_bp.route("/get_all_utilisateurs", methods=["GET"])(
    get_all_utilisateurs
)

auth_bp.route("/user", methods=["GET"])(
    get_current_user
)

auth_bp.route("/update_utilisateur/<int:id>", methods=["PUT"])(
    update_utilisateur
)

auth_bp.route("/changer_mot_de_passe", methods=["POST"])(
    changer_mot_de_passe
)

auth_bp.route("/admin/reinitialiser_mot_de_passe/<int:user_id>", methods=["POST"])(
    reinitialiser_mot_de_passe
)
