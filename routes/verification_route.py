from flask import Blueprint
from controllers.verification_controller import *

verification_bp = Blueprint('verification_bp', __name__)

verification_bp.route('/get_all_verifications', methods=['GET'])(
    get_all_verifications
)

verification_bp.route('/get_verification_by_id/<int:id>', methods=['GET'])(
    get_verification_by_id
)

verification_bp.route('/mes_verifications', methods=['GET'])(
    get_mes_verifications
)

verification_bp.route("/stat", methods=["GET"])(
    get_statistiques_verifications
)


verification_bp.route("/stat/lieu", methods=["GET"])(
    get_statistiques_verifications_par_lieu
)
