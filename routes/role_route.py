from flask import Blueprint
from controllers.role_controller import *

role_bp = Blueprint("role", __name__)

role_bp.route("/create_role", methods=["POST"])(
    create_role
)

role_bp.route("/get_role_by_id/<int:id>", methods=["GET"])(
    get_role_by_id
)

role_bp.route("/get_all_roles", methods=["GET"])(
    get_all_roles
)

role_bp.route("/update_role/<int:id>", methods=["PUT"])(
    update_role
)
 
role_bp.route("/delete_role/<int:id>", methods=["DELETE"])(
    delete_role
)
