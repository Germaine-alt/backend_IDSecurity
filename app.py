from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from config.database import db
from controllers.auth_controller import auth_bp
from controllers.face_controller import face_bp
from controllers.ocr_controller import ocr_bp
from controllers.role_controller import role_bp
from controllers.lieu_controller import lieu_bp
from controllers.type_document_controller import type_document_bp
from controllers.document_controller import document_bp
from controllers.verification_controller import verification_bp
from controllers.admin_controller import admin_bp
from services.permissions import PERMISSIONS
from werkzeug.security import generate_password_hash
from models.utilisateur import Utilisateur
from models.role import Role
from services.face_service import load_embeddings
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask_mail import Mail
from extensions import mail

#**********************************************************************************************************************
def create_initial_admin():
   
    # Vérifie si le rôle existe
    super_admin_role = Role.query.filter_by(libelle="Super-admin").first()
    if not super_admin_role:
        super_admin_role = Role(libelle="Super-admin", permissions=PERMISSIONS)
        db.session.add(super_admin_role)
        db.session.commit()

    # Vérifie si l'utilisateur admin existe déjà
    existing_admin = Utilisateur.query.filter_by(email="admin@example.com").first()
    if existing_admin:
        print("Super admin existe déjà.")
        return

    # Crée l'utilisateur admin si inexistant
    admin = Utilisateur(
        nom="Admin",
        prenom="Principal",
        email="admin@example.com",
        telephone="90000000",
        mot_passe=generate_password_hash("admin123"),
        poste="Super-admin",
        is_active=True,
        role_id=super_admin_role.id,
    )

    db.session.add(admin)
    db.session.commit()
    print("Super admin créé avec succès.")


#**********************************************************************************************************************

app = Flask(__name__)
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:92583865@localhost:3306/idsecurity"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "73e1d1e862c5475a06d587304c0dad516afc17679ab7b45b25965893c828fe98"

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


#*************************************************Configuration du mail***************************************************
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="tchallaafigermaine@gmail.com",
    MAIL_PASSWORD="nylixsuwvsdpdice",
    MAIL_DEFAULT_SENDER=("IDSecurity", "tchallaafigermaine@gmail.com")
)
mail.init_app(app)
#**************************************************************************************************************************

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(role_bp, url_prefix="/api/role")
app.register_blueprint(lieu_bp, url_prefix="/api/lieu")
app.register_blueprint(type_document_bp, url_prefix="/api/type_document")
app.register_blueprint(document_bp, url_prefix="/api/document")
app.register_blueprint(verification_bp, url_prefix="/api/verification")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(face_bp, url_prefix="/api/face")
app.register_blueprint(ocr_bp, url_prefix="/api/ocr")


@app.route("/api/uploads/<path:filename>")
def images(filename):
    return send_from_directory(os.path.join(base_dir, "uploads"), filename)


@app.route("/api/uploads_mobile/<path:filename>")
def images_mobile(filename):
    return send_from_directory(os.path.join(base_dir, "uploads_mobile"), filename)

@app.route("/api/results/<path:filename>")
def results_images(filename):
    return send_from_directory(os.path.join(base_dir, "results"), filename)

    
@app.route("/api/health")
def health_check():
    return jsonify({"message": "API IDSecurity is running", "status": "success"}), 200


@app.route("/api/init-embeddings")
def init_embeddings_route():
    """Endpoint pour initialiser les embeddings"""
    try:
        load_embeddings()
        return jsonify({"message": "Embeddings loaded successfully", "status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_initial_admin()

        load_embeddings()
        
    app.run(debug=True, use_reloader=False, port=8000)

