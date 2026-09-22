from flask import Blueprint, request, jsonify
from controllers.patient_controller import PatientController
from auth_utils import jwt_required

patient_views = Blueprint('patient_views', __name__, url_prefix='/api/patients')

@patient_views.route('', methods=['GET'])
@jwt_required()
def list_patients():
    search = request.args.get('search', '').strip()
    blood_group_id = request.args.get('blood_group_id')
    hospital_id = request.args.get('hospital_id')
    res, code = PatientController.list_patients(search, blood_group_id, hospital_id)
    return jsonify(res), code

@patient_views.route('', methods=['POST'])
@jwt_required()
def create_patient():
    data = request.get_json() or {}
    res, code = PatientController.create_patient(data)
    return jsonify(res), code

@patient_views.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    res, code = PatientController.get_patient(patient_id)
    return jsonify(res), code

@patient_views.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    data = request.get_json() or {}
    res, code = PatientController.update_patient(patient_id, data)
    return jsonify(res), code

@patient_views.route('/<int:patient_id>', methods=['DELETE'])
@jwt_required(roles=['Admin', 'Staff'])
def delete_patient(patient_id):
    res, code = PatientController.delete_patient(patient_id)
    return jsonify(res), code
