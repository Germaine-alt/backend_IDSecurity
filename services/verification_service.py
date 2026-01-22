from config.database import db
from models.verification import Verification
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func

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




    @staticmethod
    def get_user_verifications():          
        current_user_id = get_jwt_identity()          
        verifications = Verification.query.filter_by(            
            utilisateur_id=current_user_id        
            ).order_by(Verification.date_verification.desc()).all()          
        return verifications    


    @staticmethod
    def get_statistiques_verifications():
        total = db.session.query(func.count(Verification.id)).scalar()

        reussies = db.session.query(func.count(Verification.id)).filter(
            Verification.resultat_donnee == "OK"
        ).scalar()

        echouees = db.session.query(func.count(Verification.id)).filter(
            Verification.resultat_donnee == "ECHEC"
        ).scalar()

        externes = db.session.query(func.count(Verification.id)).filter(
            Verification.resultat_donnee == "EXTERNE"
        ).scalar()

        return {
            "total": total,
            "reussies": reussies,
            "echouees": echouees,
            "externes": externes
        }


    @staticmethod
    def get_stats_verifications_par_lieu():
        subquery = db.session.query(
            Verification.lieu_id,
            func.max(Verification.date_verification).label('derniere_verif')
        ).filter(
            Verification.lieu_id.isnot(None)
        ).group_by(
            Verification.lieu_id
        ).subquery()

        results = db.session.query(
            Verification.lieu_id,
            func.count(Verification.id)
        ).join(
            subquery,
            Verification.lieu_id == subquery.c.lieu_id
        ).group_by(
            Verification.lieu_id,
            subquery.c.derniere_verif
        ).order_by(
            subquery.c.derniere_verif.desc()  
        ).limit(10).all()

        data = []
        for lieu_id, total in results:
            from models.lieu import Lieu
            lieu = Lieu.query.get(lieu_id)
            if lieu:
                data.append({
                    "lieu": lieu.nom,
                    "total": total
                })

        return data