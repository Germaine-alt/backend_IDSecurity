from config.database import db
from models.lieu import Lieu
from models.verification import Verification
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, extract

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
    def get_statistiques_verifications(periode=None):
        """Récupère les statistiques avec filtrage par période"""
        query = Verification.query
        
        if periode:
            now = datetime.now()
            if periode == "today":
                # Aujourd'hui (minuit à maintenant)
                start_of_day = datetime.combine(now.date(), datetime.min.time())
                query = query.filter(Verification.date_verification >= start_of_day)
            elif periode == "yesterday":
                # Hier (toute la journée)
                yesterday = now - timedelta(days=1)
                start_of_day = datetime.combine(yesterday.date(), datetime.min.time())
                end_of_day = datetime.combine(yesterday.date(), datetime.max.time())
                query = query.filter(
                    Verification.date_verification >= start_of_day,
                    Verification.date_verification <= end_of_day
                )
            elif periode == "week":
                # 7 derniers jours
                week_ago = now - timedelta(days=7)
                query = query.filter(Verification.date_verification >= week_ago)
            elif periode == "month":
                # 30 derniers jours
                month_ago = now - timedelta(days=30)
                query = query.filter(Verification.date_verification >= month_ago)
            
        total = query.count()
        
        reussies = query.filter(
            Verification.resultat_donnee == "OK"
        ).count()

        echouees = query.filter(
            Verification.resultat_donnee == "ECHEC"
        ).count()

        externes = query.filter(
            Verification.resultat_donnee == "EXTERNE"
        ).count()

        return {
            "total": total,
            "reussies": reussies,
            "echouees": echouees,
            "externes": externes,
            "periode": periode or "all"
        }

    @staticmethod
    def get_stats_verifications_par_lieu(periode=None):
        """Récupère les statistiques par lieu avec filtrage par période"""
        query = Verification.query
        
        if periode:
            now = datetime.now()
            if periode == "today":
                start_of_day = datetime.combine(now.date(), datetime.min.time())
                query = query.filter(Verification.date_verification >= start_of_day)
            elif periode == "yesterday":
                yesterday = now - timedelta(days=1)
                start_of_day = datetime.combine(yesterday.date(), datetime.min.time())
                end_of_day = datetime.combine(yesterday.date(), datetime.max.time())
                query = query.filter(
                    Verification.date_verification >= start_of_day,
                    Verification.date_verification <= end_of_day
                )
            elif periode == "week":
                week_ago = now - timedelta(days=7)
                query = query.filter(Verification.date_verification >= week_ago)
            elif periode == "month":
                month_ago = now - timedelta(days=30)
                query = query.filter(Verification.date_verification >= month_ago)
            
        
        subquery = query.filter(
            Verification.lieu_id.isnot(None)
        ).with_entities(
            Verification.lieu_id,
            func.max(Verification.date_verification).label('derniere_verif')
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
            lieu = Lieu.query.get(lieu_id)
            if lieu:
                data.append({
                    "lieu": lieu.nom,
                    "total": total
                })

        return data

    @staticmethod
    def get_dernieres_verifications(periode=None, limit=4):
        """Récupère les dernières vérifications avec filtrage par période"""
        query = Verification.query
        
        if periode:
            now = datetime.now()
            if periode == "today":
                start_of_day = datetime.combine(now.date(), datetime.min.time())
                query = query.filter(Verification.date_verification >= start_of_day)
            elif periode == "yesterday":
                yesterday = now - timedelta(days=1)
                start_of_day = datetime.combine(yesterday.date(), datetime.min.time())
                end_of_day = datetime.combine(yesterday.date(), datetime.max.time())
                query = query.filter(
                    Verification.date_verification >= start_of_day,
                    Verification.date_verification <= end_of_day
                )
            elif periode == "week":
                week_ago = now - timedelta(days=7)
                query = query.filter(Verification.date_verification >= week_ago)
            elif periode == "month":
                month_ago = now - timedelta(days=30)
                query = query.filter(Verification.date_verification >= month_ago)
            
        
        return query.order_by(
            Verification.date_verification.desc()
        ).limit(limit).all()



    @staticmethod
    def get_statistiques_verifications_custom(start_date=None, end_date=None):
        """Récupère les statistiques avec filtrage par dates personnalisées"""
        query = Verification.query
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Verification.date_verification >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajouter 23h59 à la date de fin
            end = datetime.combine(end, datetime.max.time())
            query = query.filter(Verification.date_verification <= end)
        
        total = query.count()
        reussies = query.filter(Verification.resultat_donnee == "OK").count()
        echouees = query.filter(Verification.resultat_donnee == "ECHEC").count()
        externes = query.filter(Verification.resultat_donnee == "EXTERNE").count()

        return {
            "total": total,
            "reussies": reussies,
            "echouees": echouees,
            "externes": externes,
            "start_date": start_date,
            "end_date": end_date
        }


    @staticmethod
    def get_statistiques_verifications_custom(start_date, end_date):
        """Récupère les statistiques avec filtrage par dates personnalisées"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajouter 23h59 à la date de fin
            end = datetime.combine(end, datetime.max.time())
        except ValueError as e:
            raise ValueError(f"Format de date invalide: {str(e)}")
        
        query = Verification.query.filter(
            Verification.date_verification >= start,
            Verification.date_verification <= end
        )
        
        total = query.count()
        reussies = query.filter(Verification.resultat_donnee == "OK").count()
        echouees = query.filter(Verification.resultat_donnee == "ECHEC").count()
        externes = query.filter(Verification.resultat_donnee == "EXTERNE").count()

        return {
            "total": total,
            "reussies": reussies,
            "echouees": echouees,
            "externes": externes,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def get_stats_verifications_par_lieu_custom(start_date, end_date):
        """Récupère les statistiques par lieu avec filtrage par dates personnalisées"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = datetime.combine(end, datetime.max.time())
        except ValueError as e:
            raise ValueError(f"Format de date invalide: {str(e)}")
        
        query = Verification.query.filter(
            Verification.date_verification >= start,
            Verification.date_verification <= end
        )
        
        subquery = query.filter(
            Verification.lieu_id.isnot(None)
        ).with_entities(
            Verification.lieu_id,
            func.max(Verification.date_verification).label('derniere_verif')
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
            lieu = Lieu.query.get(lieu_id)
            if lieu:
                data.append({
                    "lieu": lieu.nom,
                    "total": total
                })

        return data

    @staticmethod
    def get_dernieres_verifications_custom(start_date, end_date, limit=4):
        """Récupère les dernières vérifications avec filtrage par dates personnalisées"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = datetime.combine(end, datetime.max.time())
        except ValueError as e:
            raise ValueError(f"Format de date invalide: {str(e)}")
        
        return Verification.query.filter(
            Verification.date_verification >= start,
            Verification.date_verification <= end
        ).order_by(
            Verification.date_verification.desc()
        ).limit(limit).all()
