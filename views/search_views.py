from flask import Blueprint, request, jsonify
from controllers.search_controller import SearchController
from auth_utils import jwt_required

search_views = Blueprint('search_views', __name__, url_prefix='/api/search')

@search_views.route('/blood', methods=['GET'])
@jwt_required()
def search_blood():
    blood_group = request.args.get('blood_group', '').strip()
    hospital_id = request.args.get('hospital_id')
    res, code = SearchController.search_blood(blood_group, hospital_id)
    return jsonify(res), code
