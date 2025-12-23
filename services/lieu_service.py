from models.lieu import Lieu
from config.database import db

class LieuService:
    @staticmethod
    def creer_lieu(nom, longitude, latitude):
        lieu = Lieu(
            nom=nom,
            longitude=longitude,
            latitude=latitude
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
    def update_lieu(id, nom, longitude, latitude):
        lieu = Lieu.query.get(id)
        lieu.nom = nom
        lieu.longitude = longitude
        lieu.latitude = latitude
        db.session.commit()
        return lieu
    
    @staticmethod
    def delete_lieu(id):
        lieu = Lieu.query.get(id)
        db.session.delete(lieu)
        db.session.commit()


