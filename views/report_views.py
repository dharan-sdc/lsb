from flask import Blueprint, request, jsonify
from controllers.report_controller import ReportController
from auth_utils import jwt_required

report_views = Blueprint('report_views', __name__, url_prefix='/api/reports')

@report_views.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    res, code = ReportController.get_dashboard_summary()
    return jsonify(res), code

@report_views.route('/donors', methods=['GET'])
@jwt_required()
def get_donor_report():
    res, code = ReportController.get_donor_report()
    return jsonify(res), code

@report_views.route('/patients', methods=['GET'])
@jwt_required()
def get_patient_report():
    res, code = ReportController.get_patient_report()
    return jsonify(res), code

@report_views.route('/donations', methods=['GET'])
@jwt_required()
def get_donation_report():
    days = int(request.args.get('days', 30))
    res, code = ReportController.get_donation_report(days)
    return jsonify(res), code

@report_views.route('/stock', methods=['GET'])
@jwt_required()
def get_stock_report():
    res, code = ReportController.get_stock_report()
    return jsonify(res), code

@report_views.route('/requests', methods=['GET'])
@jwt_required()
def get_request_report():
    res, code = ReportController.get_request_report()
    return jsonify(res), code

@report_views.route('/issues', methods=['GET'])
@jwt_required()
def get_issue_report():
    res, code = ReportController.get_issue_report()
    return jsonify(res), code
