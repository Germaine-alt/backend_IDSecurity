from models.document import Document
from services.document_service import DocumentService
from flask import jsonify, request
from flask_jwt_extended import jwt_required
import tempfile
import traceback
import pandas as pd
import os




ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS



@jwt_required()

def create_document():
    data = request.json
    numero_document = data.get("numero_document")
    nom = data.get("nom")
    prenom = data.get("prenom")
    nationalite = data.get("nationalite")
    date_de_naissance = data.get("date_de_naissance")
    sexe = data.get("sexe")
    lieu_naissance = data.get("lieu_naissance")
    date_de_delivrance = data.get("date_de_delivrance")
    date_d_expiration = data.get("date_d_expiration")
    chemin_image = data.get("chemin_image")
    taille = data.get("taille")
    poids = data.get("poids")
    profession = data.get("profession")
    domicile = data.get("domicile")
    organisme_delivrance = data.get("organisme_delivrance")
    info_nfc = data.get("info_nfc")
    type_document_id = data.get("type_document_id")
    document = DocumentService.creer_document(numero_document,nom,prenom,nationalite,date_de_naissance,sexe,lieu_naissance,date_de_delivrance,date_d_expiration,chemin_image,taille,poids,profession,domicile,organisme_delivrance,info_nfc,type_document_id)
    return jsonify({"message": "Le document a été créer avec succes", "document": document.to_dict()}), 201

@jwt_required()
def get_document_by_id(id):
    document = DocumentService.get_document_by_id(id)
    return jsonify({"message": "Le document par id", "document": document.to_dict()}), 200
    

@jwt_required()
def get_all_documents():
    documents = DocumentService.get_all_documents()
    return jsonify({"message": "La liste des documents", "documents": [document.to_dict() for document in documents]}), 200
    

@jwt_required()
def update_document(id):
    data = request.json
    numero_document = data.get("numero_document")
    nom = data.get("nom")
    prenom = data.get("prenom")
    nationalite = data.get("nationalite")
    date_de_naissance = data.get("date_de_naissance")
    sexe = data.get("sexe")
    lieu_naissance = data.get("lieu_naissance")
    date_de_delivrance = data.get("date_de_delivrance")
    date_d_expiration = data.get("date_d_expiration")
    chemin_image = data.get("chemin_image")
    taille = data.get("taille")
    poids = data.get("poids")
    profession = data.get("profession")
    domicile = data.get("domicile")
    organisme_delivrance = data.get("organisme_delivrance")
    info_nfc = data.get("info_nfc")
    type_document_id = data.get("type_document_id")    
    document = DocumentService.update_document(id,numero_document,nom,prenom,nationalite,date_de_naissance,sexe,lieu_naissance,date_de_delivrance,date_d_expiration,chemin_image,taille,poids,profession,domicile,organisme_delivrance,info_nfc,type_document_id)
    return jsonify({"message": "Le document a été modifier avec succes", "document": document.to_dict()}), 200
    

    
@jwt_required()
def delete_document(id):
    DocumentService.delete_document(id)
    return jsonify({"message": "Le document a été supprimer avec succes"}), 200




# importation

@jwt_required()
def import_documents():
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            filepath = tmp_file.name

        if file.filename.lower().endswith('.csv'):
            try:
                df = pd.read_csv(filepath, sep=';', encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, sep=';', encoding='latin1')
        else:
            df = pd.read_excel(filepath)

        # Nettoyage des noms de colonnes
        df.columns = (
            df.columns
            .str.replace('\ufeff', '', regex=False)
            .str.strip()
            .str.lower()
        )

        print("Colonnes détectées :", list(df.columns))

        # Colonnes requises
        required_columns = {'nom', 'numero_document'}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            return jsonify({
                "error": f"Colonnes manquantes dans le fichier: {', '.join(missing_columns)}",
                "colonnes_trouvees": list(df.columns)
            }), 400

        # Supprimer les lignes complètement vides
        df = df.dropna(how='all')

        # Vérifier s'il reste des données
        if df.empty:
            return jsonify({
                "error": "Le fichier ne contient aucune donnée valide",
                "imported": 0,
                "updated": 0,
                "total_processed": 0,
                "success": False
            }), 400

        imported_count = 0
        updated_count = 0
        errors = []

        # Documents existants
        existing_documents = {
            doc.numero_document: doc for doc in Document.query.all()
        }

        for index, row in df.iterrows():
            try:
                # Vérifier que les champs obligatoires ne sont pas vides
                if pd.isna(row['nom']) or str(row['nom']).strip() == '':
                    errors.append(f"Ligne {index + 2}: Le nom ne peut pas être vide")
                    continue

                if pd.isna(row['numero_document']) or str(row['numero_document']).strip() == '':
                    errors.append(f"Ligne {index + 2}: Le numero_document ne peut pas être vide")
                    continue

                nom = str(row['nom']).strip()
                numero_document = str(row['numero_document']).strip()

                # Préparer les autres champs
                def get_safe_value(row, column, default=''):
                    if column not in row.index:
                        return default
                    value = row[column]
                    if pd.isna(value):
                        return default
                    return str(value).strip()

                def parse_date(value):
                    if pd.isna(value) or str(value).strip() == '':
                        return None
                    try:
                        return pd.to_datetime(value).date()
                    except:
                        return None

                def parse_number(value):
                    if pd.isna(value) or str(value).strip() == '':
                        return None
                    try:
                        return float(value)
                    except:
                        return None

                # Vérifier si le document existe déjà
                if numero_document in existing_documents:
                    # Mise à jour
                    doc = existing_documents[numero_document]
                    doc.nom = nom
                    doc.prenom = get_safe_value(row, 'prenom')
                    doc.nationalite = get_safe_value(row, 'nationalite')
                    doc.date_de_naissance = parse_date(row.get('date_de_naissance'))
                    doc.sexe = get_safe_value(row, 'sexe')
                    doc.lieu_naissance = get_safe_value(row, 'lieu_naissance')
                    doc.date_de_delivrance = parse_date(row.get('date_de_delivrance'))
                    doc.date_d_expiration = parse_date(row.get('date_d_expiration'))
                    doc.taille = parse_number(row.get('taille'))
                    doc.poids = parse_number(row.get('poids'))
                    doc.profession = get_safe_value(row, 'profession')
                    doc.domicile = get_safe_value(row, 'domicile')
                    doc.organisme_delivrance = get_safe_value(row, 'organisme_delivrance')
                    doc.info_nfc = get_safe_value(row, 'info_nfc')
                    
                    if 'type_document_id' in row.index and not pd.isna(row['type_document_id']):
                        try:
                            doc.type_document_id = int(row['type_document_id'])
                        except:
                            pass
                    
                    updated_count += 1
                else:
                    # Création
                    type_doc_id = None
                    if 'type_document_id' in row.index and not pd.isna(row['type_document_id']):
                        try:
                            type_doc_id = int(row['type_document_id'])
                        except:
                            pass

                    document = DocumentService.creer_document(
                        numero_document=numero_document,
                        nom=nom,
                        prenom=get_safe_value(row, 'prenom'),
                        nationalite=get_safe_value(row, 'nationalite'),
                        date_de_naissance=parse_date(row.get('date_de_naissance')),
                        sexe=get_safe_value(row, 'sexe'),
                        lieu_naissance=get_safe_value(row, 'lieu_naissance'),
                        date_de_delivrance=parse_date(row.get('date_de_delivrance')),
                        date_d_expiration=parse_date(row.get('date_d_expiration')),
                        chemin_image=None,
                        taille=parse_number(row.get('taille')),
                        poids=parse_number(row.get('poids')),
                        profession=get_safe_value(row, 'profession'),
                        domicile=get_safe_value(row, 'domicile'),
                        organisme_delivrance=get_safe_value(row, 'organisme_delivrance'),
                        info_nfc=get_safe_value(row, 'info_nfc'),
                        type_document_id=type_doc_id
                    )

                    imported_count += 1
                    existing_documents[numero_document] = document

            except Exception as e:
                errors.append(f"Ligne {index + 2}: Erreur inattendue - {str(e)}")
                print(f"Erreur ligne {index + 2}:", traceback.format_exc())

        total_processed = imported_count + updated_count

        # Construire le message de retour
        if total_processed == 0:
            return jsonify({
                "error": "Aucun document n'a pu être importé. Vérifiez les données du fichier.",
                "imported": 0,
                "updated": 0,
                "total_processed": 0,
                "total_rows": len(df),
                "errors": errors,
                "success": False
            }), 400

        message_parts = []
        if imported_count > 0:
            message_parts.append(f"{imported_count} document(s) créé(s)")
        if updated_count > 0:
            message_parts.append(f"{updated_count} document(s) mis à jour")

        message = " et ".join(message_parts) + " avec succès"

        return jsonify({
            "message": message,
            "imported": imported_count,
            "updated": updated_count,
            "total_processed": total_processed,
            "total_rows": len(df),
            "errors": errors,
            "success": True
        }), 201

    except Exception as e:
        print("Erreur générale:", traceback.format_exc())
        return jsonify({
            "error": f"Erreur lors de l'import: {str(e)}",
            "success": False
        }), 500

    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)