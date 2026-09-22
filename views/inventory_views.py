from flask import Blueprint, request, jsonify
from controllers.inventory_controller import InventoryController
from auth_utils import jwt_required

inventory_views = Blueprint('inventory_views', __name__, url_prefix='/api/inventory')

@inventory_views.route('', methods=['GET'])
@jwt_required()
def get_inventory():
    res, code = InventoryController.get_inventory()
    return jsonify(res), code

@inventory_views.route('/adjust', methods=['POST'])
@jwt_required(roles=['Admin', 'Staff'])
def adjust_stock():
    data = request.get_json() or {}
    res, code = InventoryController.adjust_stock(data)
    return jsonify(res), code

@inventory_views.route('/threshold/<string:blood_group_id>', methods=['PUT'])
@jwt_required(roles=['Admin'])
def update_threshold(blood_group_id):
    data = request.get_json() or {}
    res, code = InventoryController.update_threshold(blood_group_id, data.get('threshold'))
    return jsonify(res), code

@inventory_views.route('/low-stock', methods=['GET'])
@jwt_required()
def get_low_stock():
    res, code = InventoryController.get_low_stock()
    return jsonify(res), code
