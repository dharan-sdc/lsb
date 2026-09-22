from flask import Blueprint, request, jsonify, g
from controllers.admin_controller import AdminController
from auth_utils import jwt_required

admin_views = Blueprint('admin_views', __name__, url_prefix='/api/admin')

@admin_views.route('/users', methods=['GET'])
@jwt_required(roles=['Admin'])
def list_users():
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()
    res, status_code = AdminController.list_users(search, role, status)
    return jsonify(res), status_code

@admin_views.route('/users', methods=['POST'])
@jwt_required(roles=['Admin'])
def create_user():
    data = request.get_json() or {}
    res, status_code = AdminController.create_user(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password'),
        role=data.get('role', 'Staff'),
        status=data.get('status', 'Active'),
        phone=data.get('phone', '')
    )
    return jsonify(res), status_code

@admin_views.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required(roles=['Admin'])
def update_user(user_id):
    data = request.get_json() or {}
    res, status_code = AdminController.update_user(user_id, data)
    return jsonify(res), status_code

@admin_views.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required(roles=['Admin'])
def delete_user(user_id):
    current_user_id = g.current_user.get('user_id')
    res, status_code = AdminController.delete_user(user_id, current_user_id)
    return jsonify(res), status_code

@admin_views.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required(roles=['Admin'])
def manage_role(user_id):
    data = request.get_json() or {}
    res, status_code = AdminController.manage_role(user_id, data.get('role'))
    return jsonify(res), status_code
