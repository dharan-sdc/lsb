from flask import Blueprint, request, jsonify, g
from controllers.hospital_inventory_controller import HospitalInventoryController
from auth_utils import jwt_required

hospital_inventory_views = Blueprint('hospital_inventory_views', __name__, url_prefix='/api/hospital-inventory')

@hospital_inventory_views.route('', methods=['GET'])
@jwt_required(roles=['Hospital', 'Admin', 'BloodBank'])
def get_inventory():
    hospital_id = request.args.get('hospital_id')
    # If user has role 'Hospital', auto-detect their hospital_id from current_user
    if not hospital_id and g.current_user.get('role') == 'Hospital':
        hospital_id = g.current_user.get('hospital_id') or 1
    elif not hospital_id:
        hospital_id = 1

    res, code = HospitalInventoryController.get_inventory(hospital_id)
    return jsonify(res), code

@hospital_inventory_views.route('/adjust', methods=['POST'])
@jwt_required(roles=['Hospital', 'Admin'])
def adjust_stock():
    data = request.get_json() or {}
    hospital_id = data.get('hospital_id')
    if not hospital_id and g.current_user.get('role') == 'Hospital':
        hospital_id = g.current_user.get('hospital_id') or 1
    elif not hospital_id:
        hospital_id = 1

    user_email = g.current_user.get('email', 'hospital@bloodbank.com')
    res, code = HospitalInventoryController.adjust_stock(hospital_id, data, user_email=user_email)
    return jsonify(res), code

@hospital_inventory_views.route('/issue', methods=['POST'])
@jwt_required(roles=['Hospital', 'Admin'])
def issue_to_patient():
    data = request.get_json() or {}
    hospital_id = data.get('hospital_id')
    if not hospital_id and g.current_user.get('role') == 'Hospital':
        hospital_id = g.current_user.get('hospital_id') or 1
    elif not hospital_id:
        hospital_id = 1

    user_email = g.current_user.get('email', 'hospital@bloodbank.com')
    res, code = HospitalInventoryController.issue_to_patient(hospital_id, data, user_email=user_email)
    return jsonify(res), code
