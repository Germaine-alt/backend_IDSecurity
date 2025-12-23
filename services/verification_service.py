from config.database import db
from models.verification import Verification

class VerificationService:

    @staticmethod
    def save_verification(
        utilisateur_id: int,
        lieu_id: int,
        resultat_donnee: str,
        document_id: int = None,
        ocr_result_id: int = None,
        resultat_photo: str = "NON_VERIFIE",
        url_image_echec: str = None
    ) -> Verification:

        verification = Verification(
            utilisateur_id=utilisateur_id,
            lieu_id=lieu_id,
            document_id=document_id,
            ocr_result_id=ocr_result_id,
            resultat_donnee=resultat_donnee,
            resultat_photo=resultat_photo,
            url_image_echec=url_image_echec
        )

        db.session.add(verification)
        try:
            db.session.commit()
            db.session.refresh(verification)
            print(f"✅ Verification enregistrée avec ID: {verification.id}, document_id: {document_id}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de l'enregistrement de la vérification: {e}")
            raise

        return verification


    @staticmethod
    def get_verification_by_id(id):
        return Verification.query.get(id)

    @staticmethod
    def get_all_verifications():
        return Verification.query.all()