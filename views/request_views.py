from flask import Blueprint, request, jsonify, g
from controllers.request_controller import RequestController
from auth_utils import jwt_required

request_views = Blueprint('request_views', __name__, url_prefix='/api/requests')

@request_views.route('', methods=['GET'])
@jwt_required()
def list_requests():
    role = g.current_user.get('role')
    user_id = request.args.get('user_id')
    hospital_id = request.args.get('hospital_id')

    if not user_id and role == 'User':
        user_id = g.current_user.get('user_id')
    elif not hospital_id and role == 'Hospital':
        hospital_id = g.current_user.get('hospital_id') or 1

    requester_type = request.args.get('requester_type')
    status = request.args.get('status')
    urgency = request.args.get('urgency')
    blood_group_id = request.args.get('blood_group_id')

    res, code = RequestController.list_requests(
        user_id=user_id,
        hospital_id=hospital_id,
        requester_type=requester_type,
        status=status,
        urgency=urgency,
        blood_group_id=blood_group_id
    )
    return jsonify(res), code

@request_views.route('/my-requests', methods=['GET'])
@jwt_required()
def my_requests():
    user_id = g.current_user.get('user_id')
    res, code = RequestController.list_requests(user_id=user_id)
    return jsonify(res), code

@request_views.route('', methods=['POST'])
@jwt_required()
def create_request():
    data = request.get_json() or {}
    role = g.current_user.get('role', 'User')
    requested_by = g.current_user.get('name', 'User')

    user_id = g.current_user.get('user_id') if role == 'User' else data.get('user_id')
    hospital_id = (g.current_user.get('hospital_id') or 1) if role == 'Hospital' else data.get('hospital_id')
    requester_type = 'Hospital' if role == 'Hospital' else 'User'

    res, code = RequestController.create_request(
        data,
        user_id=user_id,
        hospital_id=hospital_id,
        requester_type=requester_type,
        requested_by=requested_by
    )
    return jsonify(res), code

@request_views.route('/<int:request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    res, code = RequestController.get_request(request_id)
    return jsonify(res), code

@request_views.route('/<int:request_id>/status', methods=['PUT'])
@jwt_required(roles=['BloodBank', 'Admin'])
def update_status(request_id):
    data = request.get_json() or {}
    res, code = RequestController.update_status(
        request_id,
        data.get('status'),
        data.get('rejection_reason')
    )
    return jsonify(res), code

@request_views.route('/<int:request_id>', methods=['DELETE'])
@jwt_required(roles=['BloodBank', 'Admin'])
def delete_request(request_id):
    res, code = RequestController.delete_request(request_id)
    return jsonify(res), code
