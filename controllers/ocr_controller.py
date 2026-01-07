from flask import Blueprint, request, jsonify, current_app, url_for
from services.ocr_service import OCRService
from services.text_utils import clean_text_for_matching
from models.document import Document  
from models.ocr_result import OCRResult  
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.verification_service import VerificationService
from config.database import db
import os, json

ocr_bp = Blueprint("ocr", __name__)
UPLOAD_FOLDER = "public/uploads_mobile"
RESULT_FOLDER = "public/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

ocr_service = OCRService(langs=['fr','en','nl','de'], use_gpu=False)

@ocr_bp.route("/re_ocr", methods=["POST"])
def re_ocr():
    if "image" not in request.files:
        return jsonify(error="Aucun fichier envoyé"), 400

    file = request.files["image"]
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        results = ocr_service.process_image(save_path, preprocess=True)
        annotated = ocr_service.annotate_image(save_path, results, output_dir=RESULT_FOLDER)
        saved = ocr_service.save_result_to_db(db, OCRResult, file.filename, results, annotated)

        return jsonify({
            "status": "success",
            "text_detected": results,
            "image_annotated": annotated,
            "db_id": saved.id
        })
    except Exception as e:
        current_app.logger.exception("Erreur OCR")
        return jsonify({"status": "error", "message": str(e)}), 500


@ocr_bp.route("/ocr_compare", methods=["POST"])
@jwt_required()
def ocr_compare():
    utilisateur_id = get_jwt_identity()
    print(f"👤 Utilisateur ID depuis JWT: {utilisateur_id}")

    if "image" not in request.files:
        return jsonify(error="Aucun fichier envoyé"), 400

    file = request.files["image"]
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        # Process OCR
        results = ocr_service.process_image(save_path, preprocess=True)

        # Save annotated image
        annotated_path = ocr_service.annotate_image(
            save_path, results, output_dir=UPLOAD_FOLDER
        )

        # Build public URLs
        original_url = url_for(
            "images_mobile", 
            filename=file.filename, 
            _external=True
        )

        annotated_url = url_for(
            "images_mobile", 
            filename=os.path.basename(annotated_path), 
            _external=True
        )

        full_text = " ".join([r["text"] for r in results])
        full_text_norm = clean_text_for_matching(full_text)

        matches = ocr_service.fuzzy_match_document(
            full_text_norm, 
            db,
            Document, 
            threshold=70.0
        )

        max_confidence = max([r["confidence"] for r in results]) if results else 0.0

        # Get best document match
        best_document = None
        best_document_id = None

        if matches:
            best_document_id = matches[0]["document_id"]
            best_document = Document.query.get(best_document_id)
            print(f"✅ Match trouvé: document_id = {best_document_id}")
        else:
            print(f"❌ Aucun match trouvé, document_id sera None")

        # Create OCR result entry
        ocr_entry = OCRResult(
            image_name=file.filename,
            text_detected=full_text,
            confidence=max_confidence,
            bbox=json.dumps(results, ensure_ascii=False),
            annotated_image=annotated_url,
            document_id=best_document_id,
            utilisateur_id=utilisateur_id  
        )

        db.session.add(ocr_entry)
        db.session.commit()
        db.session.refresh(ocr_entry)

        # ✅ FIX: Only read from request.form for multipart/form-data
        lieu_id = request.form.get("lieu_id")
        print(f"📍 Lieu ID reçu: {lieu_id}")

        if not lieu_id:
            return jsonify({"status": "error", "message": "Lieu non spécifié"}), 400

        lieu_id = int(lieu_id)

        # Save verification
        verification = VerificationService.save_verification(
            utilisateur_id=utilisateur_id,
            lieu_id=lieu_id,
            document_id=best_document_id,
            ocr_result_id=ocr_entry.id,
            resultat_donnee="OK" if matches else "ECHEC",
            resultat_photo="NON_VERIFIE",
            url_image_echec=f"http://127.0.0.1:8000/api/uploads_mobile/{file.filename}"
        )
            
        # Build response
        response_data = {
            "status": "success" if matches else "not_found",
            "ocr_id": ocr_entry.id,
            "ocr_text": full_text_norm,
            "utilisateur": {
                "id": ocr_entry.utilisateur.id,
                "nom": ocr_entry.utilisateur.nom,
                "prenom": ocr_entry.utilisateur.prenom,
                "email": ocr_entry.utilisateur.email
            } if ocr_entry.utilisateur else None,
            "document": {
                "id": ocr_entry.document.id,
                "numero_document": ocr_entry.document.numero_document,
                "nom": ocr_entry.document.nom,
                "prenom": ocr_entry.document.prenom,
                "type_document": {
                    "id": ocr_entry.document.type_document.id,
                    "libelle": ocr_entry.document.type_document.libelle
                } if ocr_entry.document and ocr_entry.document.type_document else None
            } if ocr_entry.document else None,
            "original_image": original_url,
            "annotated_image": annotated_url
        }

        if matches:
            formatted = []
            for m in matches:
                formatted.append({
                    "document_id": m["document_id"],
                    "numero_document": m["numero_document"],
                    "nom": m["nom"],
                    "prenom": m["prenom"],
                    "sexe": m.get("sexe"),
                    "scores_detail": m["scores_detail"],
                    "global_similarity_score": m["global_similarity_score"],
                    "match_strength": (
                        "fort" if m["global_similarity_score"] >= 85 else
                        "moyen" if m["global_similarity_score"] >= 70 else "faible"
                    ),
                    "original_image": original_url,
                    "annotated_image": annotated_url
                })
            response_data["matches"] = formatted

        return jsonify(response_data)

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erreur OCR compare")
        return jsonify({"status": "error", "message": str(e)}), 500