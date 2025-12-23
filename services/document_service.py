from models.document import Document
from config.database import db
from datetime import datetime
import base64
import uuid
import os

class DocumentService:
    UPLOAD_FOLDER = 'public/uploads'
    
    @staticmethod
    def save_base64_image(base64_string):
        """Sauvegarde une image base64 et retourne le chemin relatif"""
        try:
            # Vérifier si c'est une image base64
            if not base64_string or not isinstance(base64_string, str):
                return None
                
            # Vérifier différents formats de base64
            if base64_string.startswith('data:image'):
                # Format: data:image/png;base64,iVBORw0KGgoAAA...
                header, data = base64_string.split(',', 1)
                # Extraire l'extension
                if 'png' in header:
                    file_extension = 'png'
                elif 'jpeg' in header or 'jpg' in header:
                    file_extension = 'jpg'
                elif 'gif' in header:
                    file_extension = 'gif'
                elif 'webp' in header:
                    file_extension = 'webp'
                else:
                    file_extension = 'png'  # extension par défaut
            else:
                # Supposer que c'est déjà un base64 pur
                data = base64_string
                file_extension = 'png'  # extension par défaut
            
            # Créer le dossier s'il n'existe pas
            os.makedirs(DocumentService.UPLOAD_FOLDER, exist_ok=True)
            
            # Générer un nom de fichier unique
            filename = f"{uuid.uuid4()}.{file_extension}"
            filepath = os.path.join(DocumentService.UPLOAD_FOLDER, filename)
            
            # Décoder et sauvegarder l'image
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(data))
            
            # Retourner uniquement le chemin relatif
            chemin_web = f"/api/uploads/{filename}"
            
            return chemin_web
            
        except Exception as e:
            print(f"Erreur sauvegarde image: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    
    @staticmethod
    def creer_document(numero_document, nom, prenom, nationalite, date_de_naissance, 
                    sexe, lieu_naissance, date_de_delivrance, date_d_expiration, 
                    chemin_image, taille, poids, profession, domicile, 
                    organisme_delivrance, info_nfc, type_document_id):
        
        # Sauvegarder l'image si c'est base64
        if chemin_image and isinstance(chemin_image, str) and (chemin_image.startswith('data:image') or len(chemin_image) > 1000):
            # Si c'est une string longue, c'est probablement base64
            saved_image_path = DocumentService.save_base64_image(chemin_image)
            if saved_image_path:
                chemin_image = saved_image_path  # Utiliser le chemin du fichier sauvegardé
            else:
                chemin_image = None
        elif chemin_image and isinstance(chemin_image, str) and chemin_image.startswith('http'):
            # Si c'est déjà une URL, la garder telle quelle
            pass
        elif chemin_image and isinstance(chemin_image, str) and chemin_image.startswith('/'):
            # Si c'est déjà un chemin relatif
            pass
        else:
            # Sinon, mettre None
            chemin_image = None
        
        # Convertir les dates si nécessaire
        def parse_date(date_value):
            if not date_value:
                return None
            if isinstance(date_value, str):
                try:
                    # Gérer différents formats de date
                    if 'T' in date_value:
                        # Format ISO: "2024-01-15T00:00:00.000Z"
                        return datetime.fromisoformat(date_value.replace('Z', '+00:00').replace('T', ' '))
                    else:
                        # Format simple: "2024-01-15"
                        return datetime.strptime(date_value, '%Y-%m-%d')
                except Exception as e:
                    print(f"Erreur parsing date: {date_value}, error: {e}")
                    return None
            return date_value
        
        date_de_naissance = parse_date(date_de_naissance)
        date_de_delivrance = parse_date(date_de_delivrance)
        date_d_expiration = parse_date(date_d_expiration)
        
        # Gérer les valeurs numériques vides
        try:
            taille = float(taille) if taille is not None and str(taille).strip() != '' else None
        except:
            taille = None
        
        try:
            poids = float(poids) if poids is not None and str(poids).strip() != '' else None
        except:
            poids = None
        
        document = Document(
            numero_document=numero_document or '',
            nom=nom or '',
            prenom=prenom or '',
            nationalite=nationalite or '',
            date_de_naissance=date_de_naissance,
            sexe=sexe or '',
            lieu_naissance=lieu_naissance or '',
            date_de_delivrance=date_de_delivrance,
            date_d_expiration=date_d_expiration,
            chemin_image=chemin_image,  
            taille=taille,
            poids=poids,
            profession=profession or '',
            domicile=domicile or '',
            organisme_delivrance=organisme_delivrance or '',
            info_nfc=info_nfc or '',
            type_document_id=type_document_id
        )
        
        try:
            db.session.add(document)
            db.session.commit()
            return document
        except Exception as e:
            db.session.rollback()
            print(f"Erreur création document: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        
    
    
    
    @staticmethod
    def get_document_by_id(id):
        return Document.query.get(id)


    @staticmethod
    def get_all_documents():
        return Document.query.all()


    @staticmethod
    def update_document(id, numero_document, nom, prenom, nationalite, date_de_naissance,
                        sexe, lieu_naissance, date_de_delivrance, date_d_expiration,
                        chemin_image, taille, poids, profession, domicile,
                        organisme_delivrance, info_nfc, type_document_id):

        document = Document.query.get(id)
        if not document:
            return None

        # Si une nouvelle image est fournie en base64
        if chemin_image and isinstance(chemin_image, str) and (chemin_image.startswith('data:image') or len(chemin_image) > 1000):
            saved_image_path = DocumentService.save_base64_image(chemin_image)
            if saved_image_path:
                chemin_image = saved_image_path
            else:
                # Garder l'ancienne image si la nouvelle échoue
                chemin_image = document.chemin_image
        elif chemin_image == '' or chemin_image is None:
            # Si l'image est vide, garder l'ancienne
            chemin_image = document.chemin_image
        
        # Même logique de parsing de dates que dans creer_document
        def parse_date(date_value):
            if not date_value:
                return None
            if isinstance(date_value, str):
                try:
                    if 'T' in date_value:
                        return datetime.fromisoformat(date_value.replace('Z', '+00:00').replace('T', ' '))
                    else:
                        return datetime.strptime(date_value, '%Y-%m-%d')
                except:
                    return None
            return date_value

        document.numero_document = numero_document or document.numero_document
        document.nom = nom or document.nom
        document.prenom = prenom or document.prenom
        document.nationalite = nationalite or document.nationalite
        document.date_de_naissance = parse_date(date_de_naissance) or document.date_de_naissance
        document.sexe = sexe or document.sexe
        document.lieu_naissance = lieu_naissance or document.lieu_naissance
        document.date_de_delivrance = parse_date(date_de_delivrance) or document.date_de_delivrance
        document.date_d_expiration = parse_date(date_d_expiration) or document.date_d_expiration
        document.chemin_image = chemin_image
        document.taille = float(taille) if taille is not None and str(taille).strip() != '' else document.taille
        document.poids = float(poids) if poids is not None and str(poids).strip() != '' else document.poids
        document.profession = profession or document.profession
        document.domicile = domicile or document.domicile
        document.organisme_delivrance = organisme_delivrance or document.organisme_delivrance
        document.info_nfc = info_nfc or document.info_nfc
        document.type_document_id = type_document_id or document.type_document_id

        try:
            db.session.commit()
            return document
        except Exception as e:
            db.session.rollback()
            print(f"Erreur mise à jour document: {e}")
            raise

    @staticmethod
    def delete_document(id):
        document = Document.query.get(id)
        db.session.delete(document)
        db.session.commit()