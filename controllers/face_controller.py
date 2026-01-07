
from services.face_service import recognize_face as recognize_face_service
from flask import Blueprint, request, jsonify


face_bp = Blueprint('face', __name__)


@face_bp.route('/recognize', methods=['POST'])
def recognize_face_api():
    print("FILES:", request.files)
    print("FORM:", request.form)
    print("CONTENT-TYPE:", request.content_type)

    try:
        # 1. Si un fichier est envoyé
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "Aucun fichier envoyé", "status": "error"}), 400

            image_bytes = file.read()
            result, code = recognize_face_service(image_bytes)
            return jsonify(result), code

        # 2. Si c'est du JSON Base64
        if request.is_json:
            data = request.get_json()
            image_base64 = data.get("image_base64")

            if not image_base64:
                return jsonify({"error": "Champ image_base64 manquant", "status": "error"}), 400

            import base64
            image_bytes = base64.b64decode(image_base64)
            result, code = recognize_face_service(image_bytes)
            return jsonify(result), code

        # 3. Rien reçu
        return jsonify({
            "error": "Aucune image valide reçue (ni fichier, ni Base64)",
            "status": "error"
        }), 415

    except Exception as e:
        return jsonify({
            "error": f"Erreur lors du traitement de la requête: {str(e)}",
            "status": "error"
        }), 500