# from flask import Blueprint

# from controllers.parametre_controller import *

# parametre_bp = Blueprint("parametre", __name__)

# # Récupérer les paramètres de l'utilisateur
# parametre_bp.route("/", methods=["GET"])(
#     get_parametres
# )

# # Mettre à jour les paramètres (tous ou partiellement)
# parametre_bp.route("/", methods=["PUT"])(
#     update_parametres
# )

# # Mettre à jour uniquement la langue
# parametre_bp.route("/langue", methods=["PUT"])(
#     update_langue
# )

# # Mettre à jour uniquement le thème
# parametre_bp.route("/theme", methods=["PUT"])(
#     update_theme
# )

# # Réinitialiser aux valeurs par défaut
# parametre_bp.route("/reset", methods=["POST"])(
#     reset_parametres
# )