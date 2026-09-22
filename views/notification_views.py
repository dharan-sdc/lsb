from flask import Blueprint, request, jsonify
from controllers.notification_controller import NotificationController
from auth_utils import jwt_required

notification_views = Blueprint('notification_views', __name__, url_prefix='/api/notifications')

@notification_views.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    res, code = NotificationController.list_notifications(unread_only)
    return jsonify(res), code

@notification_views.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    res, code = NotificationController.mark_read(notification_id)
    return jsonify(res), code

@notification_views.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    res, code = NotificationController.mark_all_read()
    return jsonify(res), code

@notification_views.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    res, code = NotificationController.delete_notification(notification_id)
    return jsonify(res), code

@notification_views.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all():
    res, code = NotificationController.clear_all()
    return jsonify(res), code
