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

verification_bp.route("/dernieres_verifications", methods=["GET"])(
    get_dernieres_verifications
)


verification_bp.route("/stat/custom", methods=["GET"])(
    get_statistiques_custom
)

verification_bp.route("/stat/lieu/custom", methods=["GET"])(
    get_stats_verifications_par_lieu_custom
)

verification_bp.route("/dernieres_verifications/custom", methods=["GET"])(
    get_dernieres_verifications_custom
)