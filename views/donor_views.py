from flask import Blueprint, request, jsonify
from controllers.donor_controller import DonorController
from auth_utils import jwt_required

donor_views = Blueprint('donor_views', __name__, url_prefix='/api/donors')

@donor_views.route('', methods=['GET'])
@jwt_required()
def list_donors():
    search = request.args.get('search', '').strip()
    blood_group_id = request.args.get('blood_group_id')
    status = request.args.get('status', '').strip()
    res, code = DonorController.list_donors(search, blood_group_id, status)
    return jsonify(res), code

@donor_views.route('', methods=['POST'])
@jwt_required()
def create_donor():
    data = request.get_json() or {}
    res, code = DonorController.create_donor(data)
    return jsonify(res), code

@donor_views.route('/<int:donor_id>', methods=['GET'])
@jwt_required()
def get_donor(donor_id):
    res, code = DonorController.get_donor(donor_id)
    return jsonify(res), code

@donor_views.route('/<int:donor_id>', methods=['PUT'])
@jwt_required()
def update_donor(donor_id):
    data = request.get_json() or {}
    res, code = DonorController.update_donor(donor_id, data)
    return jsonify(res), code

@donor_views.route('/<int:donor_id>', methods=['DELETE'])
@jwt_required(roles=['Admin', 'Staff'])
def delete_donor(donor_id):
    res, code = DonorController.delete_donor(donor_id)
    return jsonify(res), code
