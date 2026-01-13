from flask import jsonify, request 
from models.lieu import Lieu
from services.lieu_service import LieuService
from flask_jwt_extended import jwt_required
import pandas as pd
import os
import tempfile
import traceback


ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


@jwt_required()
def create_lieu():
    data = request.json
    nom = data.get("nom")
    longitude = data.get("longitude")
    latitude = data.get("latitude")
    site_id = data.get("site_id")
    lieu = LieuService.creer_lieu(nom,longitude,latitude,site_id)
    return jsonify({"message": "Le lieu a été créer avec succes", "lieu": lieu.to_dict()}), 201

@jwt_required()
def get_lieu_by_id(id):
    lieu = LieuService.get_lieu_by_id(id)
    return jsonify({"message":"lieu par id", "lieu": lieu.to_dict()}), 200


@jwt_required()
def get_all_lieux():
    lieux = LieuService.get_all_lieux()
    return jsonify({"message": "La liste des lieux","lieux":[lieu.to_dict() for lieu in lieux]}), 200


@jwt_required()
def update_lieu(id):
    data = request.json
    nom = data.get("nom")
    longitude = data.get("longitude")
    latitude = data.get("latitude")
    site_id = data.get("site_id")
    lieu = LieuService.update_lieu(id,nom,longitude,latitude,site_id)
    return jsonify({"message": "Le lieu a été modifier avec succes", "lieu": lieu.to_dict()}), 200


@jwt_required()
def delete_lieu(id):
    LieuService.delete_lieu(id)
    return jsonify({"message": "Le lieu a été supprimer avec succes"}), 200


@jwt_required()
def count_lieux():
    total = LieuService.count_lieux()
    return jsonify({
        "message" : "Nombre total de lieux",
        "total" : total
    }),200


@jwt_required()
def import_lieux():
    # Vérifier la taille du fichier
    if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
        return jsonify({"error": "Fichier trop volumineux (max 16MB)"}), 413

    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv"}), 400
    
    filepath = None
    try:
        # Sauvegarder temporairement le fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            filepath = tmp_file.name
        
        # Lire le fichier selon son type
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8')
        else:
            df = pd.read_excel(filepath)
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip().str.lower()
        
        # Vérifier les colonnes requises
        required_columns = ['nom', 'longitude', 'latitude', 'site_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                "error": f"Colonnes manquantes dans le fichier: {', '.join(missing_columns)}",
                "colonnes_requises": required_columns,
                "colonnes_trouvees": list(df.columns)
            }), 400
        
        # Supprimer les lignes vides
        df = df.dropna(how='all')
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        # Récupérer les site_id existants pour optimisation
        existing_sites = {lieu.site_id for lieu in Lieu.query.all()}
        
        for index, row in df.iterrows():
            try:
                # Vérifier que la ligne n'est pas vide
                if pd.isna(row['nom']) or str(row['nom']).strip() == '':
                    errors.append(f"Ligne {index + 2}: Le nom ne peut pas être vide")
                    continue
                
                # Extraire et valider les données
                nom = str(row['nom']).strip()
                
                try:
                    longitude = float(row['longitude'])
                except (ValueError, TypeError):
                    errors.append(f"Ligne {index + 2}: Longitude invalide ({row['longitude']})")
                    continue
                
                try:
                    latitude = float(row['latitude'])
                except (ValueError, TypeError):
                    errors.append(f"Ligne {index + 2}: Latitude invalide ({row['latitude']})")
                    continue
                
                try:
                    site_id = int(row['site_id'])
                except (ValueError, TypeError):
                    errors.append(f"Ligne {index + 2}: Site_id invalide ({row['site_id']})")
                    continue
                
                # Créer ou mettre à jour le lieu
                was_existing = site_id in existing_sites
                lieu = LieuService.creer_lieu(nom, longitude, latitude, site_id)
                
                if was_existing:
                    updated_count += 1
                else:
                    imported_count += 1
                    existing_sites.add(site_id)
                
            except ValueError as e:
                errors.append(f"Ligne {index + 2}: {str(e)}")
            except Exception as e:
                errors.append(f"Ligne {index + 2}: Erreur inattendue - {str(e)}")
        
        # Préparer le message de réponse
        total_processed = imported_count + updated_count
        message_parts = []
        
        if imported_count > 0:
            message_parts.append(f"{imported_count} lieu(x) créé(s)")
        if updated_count > 0:
            message_parts.append(f"{updated_count} lieu(x) mis à jour")
        
        if message_parts:
            message = " et ".join(message_parts) + " avec succès"
        else:
            message = "Aucun lieu n'a été importé"
        
        return jsonify({
            "message": message,
            "imported": imported_count,
            "updated": updated_count,
            "total_processed": total_processed,
            "total_rows": len(df),
            "errors": errors,
            "success": total_processed > 0
        }), 201 if total_processed > 0 else 200
        
    except pd.errors.EmptyDataError:
        return jsonify({"error": "Le fichier est vide"}), 400
    except pd.errors.ParserError as e:
        return jsonify({"error": f"Erreur lors de la lecture du fichier: format invalide"}), 400
    except Exception as e:
        print(f"Erreur d'import: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur lors du traitement du fichier: {str(e)}"}), 500
    finally:
        # Nettoyer le fichier temporaire
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier temporaire: {str(e)}")