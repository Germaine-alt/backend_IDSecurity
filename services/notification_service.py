from models.notification import Notification
from models.utilisateur import Utilisateur
from config.database import db

class NotificationService:
    
    @staticmethod
    def creer_notification(utilisateur_id, titre, message, type_notif, utilisateur_concerne_id=None):
        notification = Notification(
            utilisateur_id=utilisateur_id,
            titre=titre,
            message=message,
            type=type_notif,
            utilisateur_concerne_id=utilisateur_concerne_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def notifier_utilisateurs_avec_permission(permission, titre, message, type_notif, utilisateur_concerne_id=None):
        utilisateurs = Utilisateur.query.filter_by(is_active=True).all()
        
        notifications_creees = []
        for user in utilisateurs:
            if user.role and permission in user.role.permissions:
                notif = NotificationService.creer_notification(
                    utilisateur_id=user.id,
                    titre=titre,
                    message=message,
                    type_notif=type_notif,
                    utilisateur_concerne_id=utilisateur_concerne_id
                )
                notifications_creees.append(notif)
        
        return notifications_creees
    
    @staticmethod
    def get_notifications_utilisateur(utilisateur_id, non_lues_seulement=False):
        query = Notification.query.filter_by(utilisateur_id=utilisateur_id)
        
        if non_lues_seulement:
            query = query.filter_by(est_lu=False)
        
        return query.order_by(Notification.date_creation.desc()).all()
    
    @staticmethod
    def compter_notifications_non_lues(utilisateur_id):
        return Notification.query.filter_by(
            utilisateur_id=utilisateur_id, 
            est_lu=False
        ).count()
    
    @staticmethod
    def marquer_comme_lu(notification_id, utilisateur_id):
        notification = Notification.query.filter_by(
            id=notification_id, 
            utilisateur_id=utilisateur_id
        ).first()
        
        if notification:
            notification.est_lu = True
            db.session.commit()
            return notification
        return None
    
    @staticmethod
    def marquer_toutes_comme_lues(utilisateur_id):
        Notification.query.filter_by(
            utilisateur_id=utilisateur_id, 
            est_lu=False
        ).update({"est_lu": True})
        db.session.commit()
        return True
    
    @staticmethod
    def supprimer_notification(notification_id, utilisateur_id):
        notification = Notification.query.filter_by(
            id=notification_id, 
            utilisateur_id=utilisateur_id
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False