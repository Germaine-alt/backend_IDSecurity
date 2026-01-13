from flask import Blueprint
from controllers.document_controller import *

document_bp = Blueprint("document", __name__)

document_bp.route("/create_document", methods=["POST"])(
    create_document
)

document_bp.route("/get_document_by_id/<int:id>", methods=["GET"])(
    get_document_by_id
)

document_bp.route("/get_all_documents", methods=["GET"])(
    get_all_documents
)

document_bp.route("/update_document/<int:id>", methods=["PUT"])(
    update_document
)
  
document_bp.route("/delete_document/<int:id>", methods=["DELETE"])(
    delete_document
)
