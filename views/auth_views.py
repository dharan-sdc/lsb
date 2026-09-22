from flask import Blueprint, request, jsonify, g
from controllers.auth_controller import AuthController
from auth_utils import jwt_required

auth_views = Blueprint('auth_views', __name__, url_prefix='/api/auth')

@auth_views.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    res, status = AuthController.login(data.get('email'), data.get('password'))
    return jsonify(res), status

@auth_views.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    res, status = AuthController.register(
        data.get('name'),
        data.get('email'),
        data.get('password'),
        data.get('role', 'User'),
        data.get('phone', ''),
        blood_group_id=data.get('blood_group_id'),
        age=data.get('age'),
        gender=data.get('gender'),
        address=data.get('address'),
        hospital_id=data.get('hospital_id')
    )
    return jsonify(res), status

@auth_views.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    res, status = AuthController.forgot_password(data.get('email'))
    return jsonify(res), status

@auth_views.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    res, status = AuthController.reset_password(
        data.get('email'),
        data.get('otp'),
        data.get('new_password')
    )
    return jsonify(res), status

@auth_views.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = g.current_user.get('user_id')
    res, status = AuthController.get_current_user(user_id)
    return jsonify(res), status

@auth_views.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = g.current_user.get('user_id')
    data = request.get_json() or {}
    res, status = AuthController.update_profile(user_id, data)
    return jsonify(res), status

@auth_views.route('/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'User logged out successfully'}), 200
