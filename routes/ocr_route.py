from flask import Blueprint
from controllers.ocr_controller import *

ocr_bp = Blueprint("ocr", __name__)

ocr_bp.route("/re_ocr", methods=["POST"])(
    re_ocr
)


ocr_bp.route("/list", methods=["GET"])(
    list_externes
)


ocr_bp.route("/ocr_compare", methods=["POST"])(
    ocr_compare
)
