from flask import Blueprint, request, jsonify, g
from controllers.request_controller import RequestController
from auth_utils import jwt_required

request_views = Blueprint('request_views', __name__, url_prefix='/api/requests')

@request_views.route('', methods=['GET'])
@jwt_required()
def list_requests():
    status = request.args.get('status')
    urgency = request.args.get('urgency')
    blood_group_id = request.args.get('blood_group_id')
    hospital_id = request.args.get('hospital_id')
    res, code = RequestController.list_requests(status, urgency, blood_group_id, hospital_id)
    return jsonify(res), code

@request_views.route('', methods=['POST'])
@jwt_required()
def create_request():
    data = request.get_json() or {}
    requested_by = g.current_user.get('name', 'Staff')
    res, code = RequestController.create_request(data, requested_by=requested_by)
    return jsonify(res), code

@request_views.route('/<int:request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    res, code = RequestController.get_request(request_id)
    return jsonify(res), code

@request_views.route('/<int:request_id>/status', methods=['PUT'])
@jwt_required(roles=['Admin', 'Staff', 'Doctor'])
def update_status(request_id):
    data = request.get_json() or {}
    res, code = RequestController.update_status(
        request_id,
        data.get('status'),
        data.get('rejection_reason')
    )
    return jsonify(res), code

@request_views.route('/<int:request_id>', methods=['DELETE'])
@jwt_required(roles=['Admin'])
def delete_request(request_id):
    res, code = RequestController.delete_request(request_id)
    return jsonify(res), code
