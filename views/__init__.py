from views.auth_views import auth_views
from views.admin_views import admin_views
from views.donor_views import donor_views
from views.patient_views import patient_views
from views.blood_group_views import blood_group_views
from views.inventory_views import inventory_views
from views.donation_views import donation_views
from views.request_views import request_views
from views.issue_views import issue_views
from views.hospital_views import hospital_views
from views.search_views import search_views
from views.report_views import report_views
from views.notification_views import notification_views

def register_blueprints(app):
    app.register_blueprint(auth_views)
    app.register_blueprint(admin_views)
    app.register_blueprint(donor_views)
    app.register_blueprint(patient_views)
    app.register_blueprint(blood_group_views)
    app.register_blueprint(inventory_views)
    app.register_blueprint(donation_views)
    app.register_blueprint(request_views)
    app.register_blueprint(issue_views)
    app.register_blueprint(hospital_views)
    app.register_blueprint(search_views)
    app.register_blueprint(report_views)
    app.register_blueprint(notification_views)

