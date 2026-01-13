from flask import Blueprint
from controllers.face_controller import recognize_face_api

face_bp = Blueprint('face', __name__)

face_bp.route('/recognize', methods=['POST'])(
    recognize_face_api
)

