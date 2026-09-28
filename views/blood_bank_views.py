from flask import Blueprint, request, jsonify
from auth_utils import jwt_required
from controllers.blood_bank_profile_controller import BloodBankProfileController

blood_bank_views = Blueprint('blood_bank_views', __name__, url_prefix='/api/blood-bank')

@blood_bank_views.route('/profile', methods=['GET'])
def get_profile():
    res, status_code = BloodBankProfileController.get_profile()
    return jsonify(res), status_code

@blood_bank_views.route('/profile', methods=['PUT'])
@jwt_required(roles=['Admin', 'BloodBank'])
def update_profile():
    data = request.get_json() or {}
    res, status_code = BloodBankProfileController.update_profile(data)
    return jsonify(res), status_code
