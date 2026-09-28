from flask import Blueprint, request, jsonify
from auth_utils import jwt_required
from controllers.blood_unit_controller import BloodUnitController

unit_views = Blueprint('unit_views', __name__, url_prefix='/api/blood-units')

@unit_views.route('', methods=['GET'])
@jwt_required(roles=['Admin', 'BloodBank', 'Hospital'])
def list_units():
    blood_group_id = request.args.get('blood_group_id')
    status = request.args.get('status')
    test_status = request.args.get('test_status')
    search = request.args.get('search', '')
    expiring_soon = request.args.get('expiring_soon', '').lower() in ['true', '1']
    
    res, status_code = BloodUnitController.list_units(
        blood_group_id=blood_group_id,
        status=status,
        test_status=test_status,
        search=search,
        expiring_soon=expiring_soon
    )
    return jsonify(res), status_code

@unit_views.route('/<int:unit_id>', methods=['GET'])
@jwt_required(roles=['Admin', 'BloodBank'])
def get_unit(unit_id):
    res, status_code = BloodUnitController.get_unit(unit_id)
    return jsonify(res), status_code

@unit_views.route('', methods=['POST'])
@jwt_required(roles=['Admin', 'BloodBank'])
def create_unit():
    data = request.get_json() or {}
    res, status_code = BloodUnitController.create_unit(data)
    return jsonify(res), status_code

@unit_views.route('/<int:unit_id>/test-approval', methods=['PUT'])
@jwt_required(roles=['Admin', 'BloodBank'])
def test_approval(unit_id):
    data = request.get_json() or {}
    res, status_code = BloodUnitController.update_testing_approval(unit_id, data)
    return jsonify(res), status_code

@unit_views.route('/<int:unit_id>/discard', methods=['PUT'])
@jwt_required(roles=['Admin', 'BloodBank'])
def discard_unit(unit_id):
    data = request.get_json() or {}
    reason = data.get('reason', '')
    res, status_code = BloodUnitController.discard_unit(unit_id, reason)
    return jsonify(res), status_code
