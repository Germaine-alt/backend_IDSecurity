from models.lieu import Lieu
from config.database import db
from sqlalchemy import func

class LieuService:

    @staticmethod
    def validate_lieu_data(nom, longitude, latitude, site_id):
        """Valider les données d'un lieu"""
        errors = []
        
        if not nom or len(str(nom).strip()) == 0:
            errors.append("Le nom est obligatoire")
        
        try:
            longitude = float(longitude)
            if longitude < -180 or longitude > 180:
                errors.append("La longitude doit être entre -180 et 180")
        except (ValueError, TypeError):
            errors.append("La longitude doit être un nombre")
        
        try:
            latitude = float(latitude)
            if latitude < -90 or latitude > 90:
                errors.append("La latitude doit être entre -90 et 90")
        except (ValueError, TypeError):
            errors.append("La latitude doit être un nombre")
        
        try:
            site_id = int(site_id)
            if site_id < 0:
                errors.append("Le site_id ne peut pas être négatif")
        except (ValueError, TypeError):
            errors.append("Le site_id doit être un entier")

        return errors
    
    @staticmethod
    def creer_lieu(nom, longitude, latitude, site_id):
        # Valider les données
        errors = LieuService.validate_lieu_data(nom, longitude, latitude, site_id)
        if errors:
            raise ValueError(", ".join(errors))
        
        # Convertir les types
        try:
            site_id = int(site_id)
            longitude = float(longitude)
            latitude = float(latitude)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erreur de conversion des données: {str(e)}")
        
        # Vérifier si un lieu avec ce site_id existe déjà
        existing = Lieu.query.filter_by(site_id=site_id).first()
        if existing:
            # Mettre à jour le lieu existant
            existing.nom = str(nom).strip()
            existing.longitude = longitude
            existing.latitude = latitude
            db.session.commit()
            return existing
        
        # Créer un nouveau lieu
        lieu = Lieu(
            nom=str(nom).strip(),
            longitude=longitude,
            latitude=latitude,
            site_id=site_id
        )
        db.session.add(lieu)
        db.session.commit()
        return lieu
    
    @staticmethod
    def get_lieu_by_id(id):
        return Lieu.query.get(id)

    @staticmethod
    def get_all_lieux():
        return Lieu.query.all()


    @staticmethod
    def update_lieu(id, nom, longitude, latitude, site_id):
        lieu = Lieu.query.get(id)
        if not lieu:
            raise ValueError("Lieu non trouvé")
        
        # Valider avant de mettre à jour
        errors = LieuService.validate_lieu_data(nom, longitude, latitude, site_id)
        if errors:
            raise ValueError(", ".join(errors))
        
        lieu.nom = str(nom).strip()
        lieu.longitude = float(longitude)
        lieu.latitude = float(latitude)
        lieu.site_id = int(site_id)
        db.session.commit()
        return lieu
    
    @staticmethod
    def delete_lieu(id):
        lieu = Lieu.query.get(id)
        db.session.delete(lieu)
        db.session.commit()


    @staticmethod
    def count_lieux():
        return db.session.query(func.count(Lieu.id)).scalar()

