from flask import request, jsonify, current_app, url_for
from services.ocr_service import OCRService
from services.text_utils import clean_text_for_matching
from models.document import Document  
from models.ocr_result import OCRResult  
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.verification_service import VerificationService
from config.database import db
import os, json
from models.verification import Verification
import timeit 


UPLOAD_FOLDER = "public/uploads_mobile"
RESULT_FOLDER = "public/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

ocr_service = OCRService(langs=['fr','en'], use_gpu=False)


@jwt_required()
def re_ocr():
    utilisateur_id = get_jwt_identity()
    print(f"👤 Utilisateur ID depuis JWT: {utilisateur_id}")

    if "image" not in request.files:
        return jsonify(error="Aucun fichier envoyé"), 400

    file = request.files["image"]
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        results = ocr_service.process_image(save_path, preprocess=True)
        
        annotated_path = ocr_service.annotate_image(
            save_path, results, output_dir=UPLOAD_FOLDER
        )

        annotated_filename = os.path.basename(annotated_path)

        original_url = f"http://127.0.0.1:8000/api/uploads_mobile/{file.filename}"
        annotated_url = f"http://127.0.0.1:8000/api/uploads_mobile/{annotated_filename}"

        full_text = " ".join([r["text"] for r in results])
        max_conf = max([r["confidence"] for r in results]) if results else 0.0
        extracted = ocr_service.extract_externe_fields(results)
        
        print(f"📝 Extraction: Nom={extracted['nom']}, Prénom={extracted['prenom']}")

        ocr_entry = OCRResult(
            image_name=file.filename,
            text_detected=full_text,
            confidence=max_conf,
            bbox=json.dumps(results, ensure_ascii=False),
            annotated_image=annotated_path,
            nom_externe=extracted['nom'],
            prenom_externe=extracted['prenom'],
            utilisateur_id=utilisateur_id  
        )

        db.session.add(ocr_entry)
        db.session.commit()
        db.session.refresh(ocr_entry)

        lieu_id = request.form.get("lieu_id")
        print(f"📍 Lieu ID reçu: {lieu_id}")

        if not lieu_id:
            return jsonify({"status": "error", "message": "Lieu non spécifié"}), 400

        lieu_id = int(lieu_id)
       
        verification = Verification(
            ocr_result_id=ocr_entry.id,
            lieu_id=lieu_id,
            utilisateur_id=utilisateur_id,
            resultat_photo=f"{extracted['nom']} {extracted['prenom']}",  
            resultat_donnee='EXTERNE',  
            url_image_echec=original_url    
        )
               
        db.session.add(verification)
        db.session.commit()

        print(f"✅ Vérification créée avec url_image_echec: {original_url}")

        return jsonify({
            "status": "success",
            "verification_id": verification.id,  
            "ocr_id": ocr_entry.id,
            "nom": extracted['nom'],
            "prenom": extracted['prenom'],
            "confidence": max_conf,
            "original_image": original_url,
            "annotated_image": annotated_url,
            "lieu_id": lieu_id
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erreur OCR externe")
        return jsonify({"status": "error", "message": str(e)}), 500







@jwt_required()
def list_externes():
    """Liste uniquement les vérifications marquées comme EXTERNE"""
    try:
        from models.verification import Verification
        from models.lieu import Lieu
        from models.utilisateur import Utilisateur
        from models.ocr_result import OCRResult

        current_user_id = get_jwt_identity()
        lieu_id = request.args.get('lieu_id', type=int)
        
        print(f"📋 Externes - User ID: {current_user_id} | Lieu ID: {lieu_id}")
                
        # ✅ Requête basée sur Verification, pas OCRResult
        query = db.session.query(
            Verification,
            OCRResult,
            Lieu,
            Utilisateur
        ).join(
            OCRResult, Verification.ocr_result_id == OCRResult.id
        ).join(
            Lieu, Verification.lieu_id == Lieu.id
        ).join(
            Utilisateur, Verification.utilisateur_id == Utilisateur.id
        ).filter(
            Verification.utilisateur_id == current_user_id,
            Verification.resultat_donnee == 'EXTERNE'  # ✅ FILTRAGE CLEF !
        )
        
        if lieu_id:
            query = query.filter(Verification.lieu_id == lieu_id)

        results = query.order_by(Verification.date_verification.desc()).all()

        print(f"✅ {len(results)} externes trouvés (resultat_donnee=EXTERNE)")
        
        externes_list = []
        for verification, ocr, lieu, user in results:
            externes_list.append({
                "id": verification.id,  # ✅ ID de la verification
                "nom": ocr.nom_externe,
                "prenom": ocr.prenom_externe,
                "image_name": ocr.image_name,
                "confidence": ocr.confidence,
                "created_at": verification.date_verification.isoformat(),  # ✅ Date de verification
                "lieu": {
                    "id": lieu.id,
                    "nom": lieu.nom
                },
                "utilisateur": {
                    "id": user.id,
                    "nom": user.nom,
                    "prenom": user.prenom
                },
            })
        
        return jsonify(externes_list), 200
        
    except Exception as e:
        print(f"❌ Erreur list_externes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500






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
        results = ocr_service.process_image(save_path, preprocess=True)

        annotated_path = ocr_service.annotate_image(
            save_path, results, output_dir=UPLOAD_FOLDER
        )

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

        best_document = None
        best_document_id = None

        if matches:
            best_document_id = matches[0]["document_id"]
            best_document = Document.query.get(best_document_id)
            print(f"✅ Match trouvé: document_id = {best_document_id}")
        else:
            print(f"❌ Aucun match trouvé, document_id sera None")

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

        lieu_id = request.form.get("lieu_id")
        print(f"📍 Lieu ID reçu: {lieu_id}")

        if not lieu_id:
            return jsonify({"status": "error", "message": "Lieu non spécifié"}), 400

        lieu_id = int(lieu_id)

        verification = VerificationService.save_verification(
            utilisateur_id=utilisateur_id,
            lieu_id=lieu_id,
            document_id=best_document_id,
            ocr_result_id=ocr_entry.id,
            resultat_donnee="OK" if matches else "ECHEC",
            resultat_photo="NON_VERIFIE",
            url_image_echec=f"http://127.0.0.1:8000/api/uploads_mobile/{file.filename}"
        )

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



