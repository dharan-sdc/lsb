from flask import Blueprint, request, jsonify
from auth_utils import jwt_required
from controllers.import_controller import ImportController

import_views = Blueprint('import_views', __name__, url_prefix='/api/import')

@import_views.route('/preview', methods=['POST'])
@jwt_required(roles=['Admin', 'BloodBank'])
def preview_import():
    data = request.get_json() or {}
    data_type = data.get('data_type', 'donors')
    items = data.get('items', [])
    res, status_code = ImportController.preview_import(data_type, items)
    return jsonify(res), status_code

@import_views.route('/execute', methods=['POST'])
@jwt_required(roles=['Admin', 'BloodBank'])
def execute_import():
    data = request.get_json() or {}
    data_type = data.get('data_type', 'donors')
    items = data.get('items', [])
    res, status_code = ImportController.execute_import(data_type, items)
    return jsonify(res), status_code
