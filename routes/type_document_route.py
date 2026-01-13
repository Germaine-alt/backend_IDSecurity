from flask import Blueprint
from controllers.type_document_controller import *

type_document_bp = Blueprint("type_document", __name__)

type_document_bp.route("/create_type_document", methods=["POST"])(
    create_type_document
)

type_document_bp.route("/get_type_document_by_id/<int:id>", methods=["GET"])(
    get_type_document_by_id
)
  
type_document_bp.route("/get_all_type_documents", methods=["GET"])(
    get_all_type_documents
)
 
type_document_bp.route("/update_type_document/<int:id>", methods=["PUT"])(
    update_type_document
)
    
type_document_bp.route("/delete_type_document/<int:id>", methods=["DELETE"])(
    delete_type_document
)

