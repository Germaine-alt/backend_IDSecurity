# from models.parametre import Parametre
# from config.database import db


# class ParametreService:
#     """Service pour gérer les paramètres de personnalisation des utilisateurs"""

#     @staticmethod
#     def get_parametres(utilisateur_id):
#         """Récupérer les paramètres d'un utilisateur"""
#         parametres = Parametre.query.filter_by(utilisateur_id=utilisateur_id).first()
        
#         # Si l'utilisateur n'a pas encore de paramètres, les créer avec les valeurs par défaut
#         if not parametres:
#             parametres = Parametre.creer_parametres_defaut(utilisateur_id)
        
#         return parametres

#     @staticmethod
#     def creer_parametres_defaut(utilisateur_id):
#         """Créer les paramètres par défaut pour un utilisateur"""
#         parametres = Parametre(
#             utilisateur_id=utilisateur_id,
#             langue='fr',
#             theme='light',
#         )
#         db.session.add(parametres)
#         db.session.commit()
#         return parametres

#     @staticmethod
#     def update_parametres(utilisateur_id, langue=None, theme=None):
#         """Mettre à jour les paramètres d'un utilisateur"""
#         parametres = Parametre.query.filter_by(utilisateur_id=utilisateur_id).first()
        
#         # Si les paramètres n'existent pas, les créer
#         if not parametres:
#             parametres = Parametre(utilisateur_id=utilisateur_id)
#             db.session.add(parametres)
        
#         # Mettre à jour uniquement les champs fournis
#         if langue is not None and langue in ['fr', 'en']:
#             parametres.langue = langue
        
#         if theme is not None and theme in ['light', 'dark']:
#             parametres.theme = theme
        
        
        
#         db.session.commit()
#         return parametres

#     @staticmethod
#     def reset_parametres(utilisateur_id):
#         """Réinitialiser les paramètres aux valeurs par défaut"""
#         parametres = Parametre.query.filter_by(utilisateur_id=utilisateur_id).first()
        
#         if parametres:
#             parametres.langue = 'fr'
#             parametres.theme = 'light'
#             db.session.commit()
#         else:
#             parametres = Parametre.creer_parametres_defaut(utilisateur_id)
        
#         return parametres

#     @staticmethod
#     def update_langue(utilisateur_id, langue):
#         """Mettre à jour uniquement la langue"""
#         if langue not in ['fr', 'en']:
#             return None, "Langue invalide. Utiliser 'fr' ou 'en'."
        
#         parametres = Parametre.update_parametres(utilisateur_id, langue=langue)
#         return parametres, None

#     @staticmethod
#     def update_theme(utilisateur_id, theme):
#         """Mettre à jour uniquement le thème"""
#         if theme not in ['light', 'dark']:
#             return None, "Thème invalide. Utiliser 'light' ou 'dark'."
        
#         parametres = Parametre.update_parametres(utilisateur_id, theme=theme)
#         return parametres, None

    