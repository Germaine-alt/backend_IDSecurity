from flask import Blueprint
from controllers.lieu_controller import *

lieu_bp = Blueprint("lieu", __name__)

lieu_bp.route("/create_lieu", methods=["POST"])(
    create_lieu
)

lieu_bp.route("/get_lieu_by_id/<int:id>", methods=["GET"])(
    get_lieu_by_id
)

lieu_bp.route("/get_all_lieux", methods=["GET"])(
    get_all_lieux)

lieu_bp.route("/update_lieu/<int:id>", methods=["PUT"])(
    update_lieu
)

lieu_bp.route("/delete_lieu/<int:id>", methods=["DELETE"])(
    delete_lieu
)

lieu_bp.route("/count_lieux", methods=["GET"])(
    count_lieux
)

lieu_bp.route("/import_lieux", methods=["POST"])(
    import_lieux
)

