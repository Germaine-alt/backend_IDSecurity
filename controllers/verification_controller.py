from flask import request, jsonify , send_file
from flask_jwt_extended import jwt_required
from services.verification_service import VerificationService
from datetime import datetime, timedelta


@jwt_required()
def get_all_verifications():
    verifications = VerificationService.get_all_verifications()
    return jsonify({"message": "La liste des verifications", "verifications": [verification.to_dict() for verification in verifications]}), 200
    
@jwt_required()
def get_verification_by_id(id):
    verification = VerificationService.get_verification_by_id(id)
    return jsonify({"message": "La verification par id", "verification": verification.to_dict()}), 200


@jwt_required()
def get_mes_verifications():
    try:
        verifications = VerificationService.get_user_verifications()
        if not verifications:
            return jsonify({
                "message": "Aucune vérification trouvée",
                "verification": []
            }),200
        return jsonify({
            "message": "Liste des verifications de l'utilisateur",
            "verifications": [verification.to_dict() for verification in verifications],
            "total": len(verifications)
        }),200
    except Exception as e:        
        return jsonify({            
            "message": f"Erreur lors de la recuperation des verifications: {str(e)}"        
    }), 500      


@jwt_required()
def get_statistiques_verifications():
    periode = request.args.get('periode', default=None, type=str)
    stats = VerificationService.get_statistiques_verifications(periode)
    return jsonify({
        "message": "Statistiques des vérifications",
        "statistiques": stats
    }), 200

@jwt_required()
def get_statistiques_verifications_par_lieu():
    periode = request.args.get('periode', default=None, type=str)
    stats = VerificationService.get_stats_verifications_par_lieu(periode)
    return jsonify({
        "message": "Statistiques des vérifications par lieu",
        "data": stats
    }), 200

@jwt_required()
def get_dernieres_verifications():
    periode = request.args.get('periode', default=None, type=str)
    limit = request.args.get('limit', default=4, type=int)
    verifications = VerificationService.get_dernieres_verifications(periode, limit)
    return jsonify({
        "message": "Dernières vérifications",
        "verifications": [v.to_dict() for v in verifications]
    }), 200

@jwt_required()
def get_statistiques_custom():
    start_date = request.args.get('start_date', default=None, type=str)
    end_date = request.args.get('end_date', default=None, type=str)
    
    if not start_date or not end_date:
        return jsonify({"error": "Les dates de début et de fin sont requises"}), 400
    
    stats = VerificationService.get_statistiques_verifications_custom(start_date, end_date)
    return jsonify({
        "message": "Statistiques personnalisées",
        "statistiques": stats
    }), 200

@jwt_required()
def get_stats_verifications_par_lieu_custom():
    start_date = request.args.get('start_date', default=None, type=str)
    end_date = request.args.get('end_date', default=None, type=str)
    
    if not start_date or not end_date:
        return jsonify({"error": "Les dates de début et de fin sont requises"}), 400
    
    stats = VerificationService.get_stats_verifications_par_lieu_custom(start_date, end_date)
    return jsonify({
        "message": "Statistiques des vérifications par lieu (personnalisé)",
        "data": stats
    }), 200

@jwt_required()
def get_dernieres_verifications_custom():
    start_date = request.args.get('start_date', default=None, type=str)
    end_date = request.args.get('end_date', default=None, type=str)
    limit = request.args.get('limit', default=4, type=int)
    
    if not start_date or not end_date:
        return jsonify({"error": "Les dates de début et de fin sont requises"}), 400
    
    verifications = VerificationService.get_dernieres_verifications_custom(start_date, end_date, limit)
    return jsonify({
        "message": "Dernières vérifications (personnalisé)",
        "verifications": [v.to_dict() for v in verifications]
    }), 200



# Exportation

@jwt_required()
def export_verifications_excel():
    """
    Exporte toutes les vérifications vers un fichier Excel
    """
    try:
        # Récupérer les paramètres
        periode = request.args.get('periode', default=None, type=str)
        start_date = request.args.get('start_date', default=None, type=str)
        end_date = request.args.get('end_date', default=None, type=str)
        
        print(f"📊 Export demandé - Période: {periode}, Dates: {start_date} à {end_date}")
        
        # Récupérer les vérifications
        if start_date and end_date:
            verifications = VerificationService.get_verifications_for_export_custom(start_date, end_date)
            filename_date = f"{start_date}_to_{end_date}"
        elif periode:
            verifications = VerificationService.get_verifications_for_export(periode)
            filename_date = periode
        else:
            verifications = VerificationService.get_all_verifications()
            filename_date = "all"
        
        print(f"✅ {len(verifications)} vérifications récupérées")
        
        if not verifications:
            return jsonify({"message": "Aucune vérification à exporter"}), 404
        
        # Générer le fichier Excel
        excel_buffer = VerificationService.export_verifications_to_excel(verifications)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"verifications_{filename_date}_{timestamp}.xlsx"
        
        print(f"✅ Fichier Excel généré: {filename}")
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except ValueError as e:
        print(f"❌ Erreur de validation: {str(e)}")
        return jsonify({"error": f"Erreur de format: {str(e)}"}), 400
    except Exception as e:
        print(f"❌ Erreur serveur: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500