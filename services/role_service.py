from models.role import Role
from config.database import db
from services.permissions import PERMISSIONS

class RoleService:
    @staticmethod
    def creer_role(libelle, permissions=None):
        if permissions is None:
            permissions = []

        role = Role(
            libelle=libelle,
            permissions=permissions
        )
        db.session.add(role)
        db.session.commit()
        return role


    @staticmethod
    def get_role_by_id(id):
        return Role.query.get(id)


    @staticmethod
    def get_all_roles():
        return Role.query.all()


    @staticmethod
    def update_role(id,libelle,permissions):
        role = Role.query.get(id)
        role.libelle = libelle
        role.permissions = permissions
        db.session.commit()
        return role


    @staticmethod
    def delete_role(id):
        role = Role.query.get(id)
        db.session.delete(role)
        db.session.commit()


