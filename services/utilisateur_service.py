from werkzeug.security import generate_password_hash, check_password_hash
from models.utilisateur import Utilisateur
from config.database import db
from services.mail_service import envoyer_mail_activation
from services.password_utils import generer_mot_de_passe

class UtilisateurService:
    @staticmethod
    def creer_utilisateur(nom, prenom, email, poste, telephone, role_id):
        user = Utilisateur(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            poste=poste,
            role_id=role_id,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def verifier_connexion(email, mot_passe):
        user = Utilisateur.query.filter_by(email=email).first()
        if user and check_password_hash(user.mot_passe, mot_passe):
            if user.is_active:
                return user
        return None


    @staticmethod
    def basculer_activation(user_id):
        user = Utilisateur.query.get(user_id)
        if not user:
            return None

        # Si on active le compte
        if not user.is_active:
            mot_passe_temp = generer_mot_de_passe()
            user.mot_passe = generate_password_hash(mot_passe_temp)
            user.is_active = True
            db.session.commit()

            envoyer_mail_activation(user, mot_passe_temp)
        else:
            user.is_active = False
            db.session.commit()

        return user



    @staticmethod
    def get_all_utilisateurs():
        return Utilisateur.query.all()


    @staticmethod
    def get_user(user_id):
        user = Utilisateur.query.get(user_id)
        return user



    @staticmethod
    def desactiver(user_id):
        user = Utilisateur.query.get(user_id)
        if not user:
            return None
        user.is_active = False
        db.session.commit()
        return user


    @staticmethod
    def update_utilisateur(user_id, nom=None, prenom=None, email=None, telephone=None, mot_passe=None, poste=None, role_id=None):
        user = Utilisateur.query.get(user_id)
        if not user:
            return None
        if nom is not None:
            user.nom = nom
        if prenom is not None:
            user.prenom = prenom
        if email is not None:
            user.email = email
        if telephone is not None:
            user.telephone = telephone
        if poste is not None:
            user.poste = poste
        if role_id is not None:
            user.role_id = role_id
        if mot_passe is not None:
            user.mot_passe = generate_password_hash(mot_passe)

        db.session.commit()
        return user   



    
    @staticmethod
    def changer_mot_de_passe(user_id, ancien_mot_passe, nouveau_mot_passe):
        """Change le mot de passe de l'utilisateur après vérification"""
        user = Utilisateur.query.get(user_id)
        if not user:
            return None, "Utilisateur non trouvé"
        
        # Vérifier l'ancien mot de passe
        if not check_password_hash(user.mot_passe, ancien_mot_passe):
            return None, "Ancien mot de passe incorrect"
        
        # Vérifier que le nouveau mot de passe est différent de l'ancien
        if check_password_hash(user.mot_passe, nouveau_mot_passe):
            return None, "Le nouveau mot de passe doit être différent de l'ancien"
        
        # Mettre à jour le mot de passe
        user.mot_passe = generate_password_hash(nouveau_mot_passe)
        db.session.commit()
        
        return user, None
    
    @staticmethod
    def reinitialiser_mot_de_passe(user_id):
        """Réinitialise le mot de passe (pour admin)"""
        user = Utilisateur.query.get(user_id)
        if not user:
            return None, "Utilisateur non trouvé"
        
        # Générer un nouveau mot de passe temporaire
        mot_passe_temp = generer_mot_de_passe()
        user.mot_passe = generate_password_hash(mot_passe_temp)
        db.session.commit()
        
        return mot_passe_temp, None