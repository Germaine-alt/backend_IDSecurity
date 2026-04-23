# from flask_jwt_extended import jwt_required, get_jwt_identity
# from flask import jsonify, request

# from services.parametre_service import ParametreService



# @jwt_required()
# def get_parametres():
#     """Récupérer les paramètres de l'utilisateur connecté"""
#     try:
#         utilisateur_id = get_jwt_identity()
#         parametres = ParametreService.get_parametres(utilisateur_id)
        
#         return jsonify({
#             "message": "Paramètres récupérés avec succès",
#             "parametres": parametres.to_dict()
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             "message": "Erreur lors de la récupération des paramètres",
#             "error": str(e)
#         }), 500


# @jwt_required()
# def update_parametres():
#     """Mettre à jour les paramètres de l'utilisateur"""
#     try:
#         utilisateur_id = get_jwt_identity()
#         data = request.get_json()
        
#         # Validation des données
#         langue = data.get('langue')
#         theme = data.get('theme')
        
#         # Valider la langue
#         if langue is not None and langue not in ['fr', 'en']:
#             return jsonify({
#                 "message": "Langue invalide. Utiliser 'fr' ou 'en'."
#             }), 400
        
#         # Valider le thème
#         if theme is not None and theme not in ['light', 'dark']:
#             return jsonify({
#                 "message": "Thème invalide. Utiliser 'light' ou 'dark'."
#             }), 400
        
#         # Mettre à jour les paramètres
#         parametres = ParametreService.update_parametres(
#             utilisateur_id=utilisateur_id,
#             langue=langue,
#             theme=theme,
#         )
        
#         return jsonify({
#             "message": "Paramètres mis à jour avec succès",
#             "parametres": parametres.to_dict()
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             "message": "Erreur lors de la mise à jour des paramètres",
#             "error": str(e)
#         }), 500


# @jwt_required()
# def update_langue():
#     """Mettre à jour uniquement la langue"""
#     try:
#         utilisateur_id = get_jwt_identity()
#         data = request.get_json()
#         langue = data.get('langue')
        
#         if not langue:
#             return jsonify({"message": "Langue requise"}), 400
        
#         parametres, error = ParametreService.update_langue(utilisateur_id, langue)
        
#         if error:
#             return jsonify({"message": error}), 400
        
#         return jsonify({
#             "message": "Langue mise à jour avec succès",
#             "parametres": parametres.to_dict()
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             "message": "Erreur lors de la mise à jour de la langue",
#             "error": str(e)
#         }), 500


# @jwt_required()
# def update_theme():
#     """Mettre à jour uniquement le thème"""
#     try:
#         utilisateur_id = get_jwt_identity()
#         data = request.get_json()
#         theme = data.get('theme')
        
#         if not theme:
#             return jsonify({"message": "Thème requis"}), 400
        
#         parametres, error = ParametreService.update_theme(utilisateur_id, theme)
        
#         if error:
#             return jsonify({"message": error}), 400
        
#         return jsonify({
#             "message": "Thème mis à jour avec succès",
#             "parametres": parametres.to_dict()
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             "message": "Erreur lors de la mise à jour du thème",
#             "error": str(e)
#         }), 500




# @jwt_required()
# def reset_parametres():
#     """Réinitialiser les paramètres aux valeurs par défaut"""
#     try:
#         utilisateur_id = get_jwt_identity()
#         parametres = ParametreService.reset_parametres(utilisateur_id)
        
#         return jsonify({
#             "message": "Paramètres réinitialisés avec succès",
#             "parametres": parametres.to_dict()
#         }), 200
    
#     except Exception as e:
#         return jsonify({
#             "message": "Erreur lors de la réinitialisation des paramètres",
#             "error": str(e)
#         }), 500