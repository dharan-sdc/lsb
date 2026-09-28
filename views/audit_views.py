from flask import Blueprint, request, jsonify
from auth_utils import jwt_required
from controllers.audit_controller import AuditController

audit_views = Blueprint('audit_views', __name__, url_prefix='/api/audit-logs')

@audit_views.route('', methods=['GET'])
@jwt_required(roles=['Admin', 'BloodBank'])
def list_logs():
    module = request.args.get('module', '')
    action = request.args.get('action', '')
    search = request.args.get('search', '')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    res, status_code = AuditController.get_logs(module=module, action=action, search=search, limit=limit, offset=offset)
    return jsonify(res), status_code
