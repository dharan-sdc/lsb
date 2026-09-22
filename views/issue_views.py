from flask import Blueprint, request, jsonify, g
from controllers.issue_controller import IssueController
from auth_utils import jwt_required

issue_views = Blueprint('issue_views', __name__, url_prefix='/api/issues')

@issue_views.route('', methods=['GET'])
@jwt_required()
def list_issues():
    res, code = IssueController.list_issues()
    return jsonify(res), code

@issue_views.route('', methods=['POST'])
@jwt_required(roles=['Admin', 'Staff', 'Doctor'])
def issue_blood():
    data = request.get_json() or {}
    issued_by = g.current_user.get('name', 'Staff')
    res, code = IssueController.issue_blood(data, issued_by=issued_by)
    return jsonify(res), code

@issue_views.route('/<int:issue_id>', methods=['GET'])
@jwt_required()
def get_issue(issue_id):
    res, code = IssueController.get_issue(issue_id)
    return jsonify(res), code
