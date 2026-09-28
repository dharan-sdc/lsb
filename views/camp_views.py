from flask import Blueprint, request, jsonify, g
from auth_utils import jwt_required
from controllers.camp_controller import CampController

camp_views = Blueprint('camp_views', __name__, url_prefix='/api/camps')

@camp_views.route('', methods=['GET'])
def list_camps():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    res, status_code = CampController.list_camps(search=search, status=status)
    return jsonify(res), status_code

@camp_views.route('/<int:camp_id>', methods=['GET'])
def get_camp(camp_id):
    res, status_code = CampController.get_camp(camp_id)
    return jsonify(res), status_code

@camp_views.route('', methods=['POST'])
@jwt_required(roles=['Admin', 'BloodBank'])
def create_camp():
    data = request.get_json() or {}
    res, status_code = CampController.create_camp(data)
    return jsonify(res), status_code

@camp_views.route('/<int:camp_id>', methods=['PUT'])
@jwt_required(roles=['Admin', 'BloodBank'])
def update_camp(camp_id):
    data = request.get_json() or {}
    res, status_code = CampController.update_camp(camp_id, data)
    return jsonify(res), status_code

@camp_views.route('/<int:camp_id>', methods=['DELETE'])
@jwt_required(roles=['Admin', 'BloodBank'])
def delete_camp(camp_id):
    res, status_code = CampController.delete_camp(camp_id)
    return jsonify(res), status_code

@camp_views.route('/<int:camp_id>/register', methods=['POST'])
@jwt_required()
def register_donor(camp_id):
    data = request.get_json() or {}
    user_id = g.current_user.get('user_id')
    res, status_code = CampController.register_donor_for_camp(camp_id, data, user_id=user_id)
    return jsonify(res), status_code

@camp_views.route('/registrations/<int:reg_id>/screen', methods=['PUT'])
@jwt_required(roles=['Admin', 'BloodBank'])
def update_screening(reg_id):
    data = request.get_json() or {}
    res, status_code = CampController.update_screening_status(reg_id, data)
    return jsonify(res), status_code

@camp_views.route('/my-registrations', methods=['GET'])
@jwt_required()
def get_my_registrations():
    user_id = g.current_user.get('user_id')
    res, status_code = CampController.get_user_registrations(user_id)
    return jsonify(res), status_code

@camp_views.route('/registrations/<int:reg_id>/cancel', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def cancel_registration(reg_id):
    user_id = g.current_user.get('user_id')
    role = g.current_user.get('role', 'User')
    res, status_code = CampController.cancel_registration(reg_id, user_id=user_id, user_role=role)
    return jsonify(res), status_code

@camp_views.route('/donor-eligibility', methods=['GET'])
@jwt_required()
def get_donor_eligibility():
    user_id = g.current_user.get('user_id')
    res, status_code = CampController.get_donor_eligibility(user_id=user_id)
    return jsonify(res), status_code
