from flask import Blueprint, request, jsonify, g
from controllers.donation_controller import DonationController
from auth_utils import jwt_required

donation_views = Blueprint('donation_views', __name__, url_prefix='/api/donations')

@donation_views.route('', methods=['GET'])
@jwt_required()
def list_donations():
    user_id = request.args.get('user_id')
    # If standard User, default to showing their own donations
    if not user_id and g.current_user.get('role') == 'User':
        user_id = g.current_user.get('user_id')

    donor_id = request.args.get('donor_id')
    blood_group_id = request.args.get('blood_group_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    res, code = DonationController.list_donations(
        user_id=user_id,
        donor_id=donor_id,
        blood_group_id=blood_group_id,
        date_from=date_from,
        date_to=date_to
    )
    return jsonify(res), code

@donation_views.route('/my-donations', methods=['GET'])
@jwt_required()
def my_donations():
    user_id = g.current_user.get('user_id')
    res, code = DonationController.list_donations(user_id=user_id)
    return jsonify(res), code

@donation_views.route('', methods=['POST'])
@jwt_required(roles=['User', 'BloodBank', 'Admin'])
def register_donation():
    data = request.get_json() or {}
    role = g.current_user.get('role')
    user_id = g.current_user.get('user_id') if role == 'User' else data.get('user_id')
    recorded_by = g.current_user.get('name', 'BloodBank Staff')
    res, code = DonationController.register_donation(data, user_id=user_id, recorded_by=recorded_by)
    return jsonify(res), code

@donation_views.route('/<int:donation_id>', methods=['GET'])
@jwt_required()
def get_donation(donation_id):
    res, code = DonationController.get_donation(donation_id)
    return jsonify(res), code

@donation_views.route('/<int:donation_id>', methods=['DELETE'])
@jwt_required(roles=['Admin', 'BloodBank'])
def delete_donation(donation_id):
    res, code = DonationController.delete_donation(donation_id)
    return jsonify(res), code
