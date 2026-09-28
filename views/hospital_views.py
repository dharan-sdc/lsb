from flask import Blueprint, request, jsonify
from controllers.hospital_controller import HospitalController
from auth_utils import jwt_required

hospital_views = Blueprint('hospital_views', __name__, url_prefix='/api/hospitals')

@hospital_views.route('', methods=['GET'])
@jwt_required()
def list_hospitals():
    search = request.args.get('search', '').strip()
    hospital_type = request.args.get('hospital_type', '').strip()
    res, code = HospitalController.list_hospitals(search, hospital_type)
    return jsonify(res), code

@hospital_views.route('', methods=['POST'])
@jwt_required(roles=['Admin'])
def create_hospital():
    data = request.get_json() or {}
    res, code = HospitalController.create_hospital(data)
    return jsonify(res), code

@hospital_views.route('/dashboard', methods=['GET'])
@jwt_required()
def get_current_hospital_dashboard():
    from flask import g
    role = g.current_user.get('role')
    hospital_id = request.args.get('hospital_id')
    if not hospital_id and role == 'Hospital':
        hospital_id = g.current_user.get('hospital_id') or 1
    elif not hospital_id:
        hospital_id = 1
    res, code = HospitalController.get_dashboard_stats(int(hospital_id))
    return jsonify(res), code

@hospital_views.route('/<int:hospital_id>/dashboard', methods=['GET'])
@jwt_required()
def get_hospital_dashboard(hospital_id):
    res, code = HospitalController.get_dashboard_stats(hospital_id)
    return jsonify(res), code

@hospital_views.route('/<int:hospital_id>', methods=['GET'])
@jwt_required()
def get_hospital(hospital_id):
    res, code = HospitalController.get_hospital(hospital_id)
    return jsonify(res), code

@hospital_views.route('/<int:hospital_id>', methods=['PUT'])
@jwt_required()
def update_hospital(hospital_id):
    data = request.get_json() or {}
    res, code = HospitalController.update_hospital(hospital_id, data)
    return jsonify(res), code

@hospital_views.route('/<int:hospital_id>', methods=['DELETE'])
@jwt_required(roles=['Admin'])
def delete_hospital(hospital_id):
    res, code = HospitalController.delete_hospital(hospital_id)
    return jsonify(res), code
