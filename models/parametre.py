# from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
# from sqlalchemy.orm import relationship
# from config.database import db

# class Parametre(db.Model):
#     __tablename__ = "parametres"

#     id = Column(Integer, primary_key=True)
#     utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), unique=True, nullable=False)
#     langue = Column(String(2), default='fr')  # 'fr' ou 'en'
#     theme = Column(String(10), default='light')  # 'light' ou 'dark'


#     utilisateur = relationship("Utilisateur", back_populates="parametres")

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "utilisateur_id": self.utilisateur_id,
#             "langue": self.langue,
#             "theme": self.theme,
#             "mini_sidebar": self.mini_sidebar
#         }

#     @staticmethod
#     def get_default_settings():
#         """Retourne les paramètres par défaut"""
#         return {
#             "langue": "fr",
#             "theme": "light",
#             "mini_sidebar": False
#         }