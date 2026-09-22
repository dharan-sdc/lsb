from flask import Blueprint, request, jsonify
from controllers.blood_group_controller import BloodGroupController
from auth_utils import jwt_required

blood_group_views = Blueprint('blood_group_views', __name__, url_prefix='/api/blood-groups')

@blood_group_views.route('', methods=['GET'])
@jwt_required()
def list_blood_groups():
    res, code = BloodGroupController.list_blood_groups()
    return jsonify(res), code

@blood_group_views.route('/<int:group_id>', methods=['GET'])
@jwt_required()
def get_blood_group(group_id):
    res, code = BloodGroupController.get_blood_group(group_id)
    return jsonify(res), code

@blood_group_views.route('', methods=['POST'])
@jwt_required(roles=['Admin'])
def create_blood_group():
    data = request.get_json() or {}
    res, code = BloodGroupController.create_blood_group(data)
    return jsonify(res), code

@blood_group_views.route('/<int:group_id>', methods=['PUT'])
@jwt_required(roles=['Admin'])
def update_blood_group(group_id):
    data = request.get_json() or {}
    res, code = BloodGroupController.update_blood_group(group_id, data)
    return jsonify(res), code

@blood_group_views.route('/<int:group_id>', methods=['DELETE'])
@jwt_required(roles=['Admin'])
def delete_blood_group(group_id):
    res, code = BloodGroupController.delete_blood_group(group_id)
    return jsonify(res), code

@blood_group_views.route('/compatibility', methods=['GET'])
@jwt_required()
def get_compatibility():
    res, code = BloodGroupController.get_compatibility()
    return jsonify(res), code
