from sqlalchemy import func
from datetime import datetime, timedelta, timezone, date
from database import get_db
from models import Donor, Patient, BloodGroup, BloodInventory, BloodDonation, BloodRequest, BloodIssue, Hospital, User

class ReportController:
    @staticmethod
    def get_dashboard_summary():
        with get_db() as db:
            total_donors = db.query(Donor).count()
            total_patients = db.query(Patient).count()
            total_hospitals = db.query(Hospital).count()
            total_users = db.query(User).count()

            inventories = db.query(BloodInventory).all()
            total_stock_units = sum(inv.units_available for inv in inventories)
            total_stock_ml = sum(inv.total_ml for inv in inventories)
            low_stock_groups = sum(1 for inv in inventories if inv.units_available <= inv.low_stock_threshold)

            pending_requests = db.query(BloodRequest).filter(BloodRequest.status == 'Pending').count()
            approved_requests = db.query(BloodRequest).filter(BloodRequest.status == 'Approved').count()
            completed_requests = db.query(BloodRequest).filter(BloodRequest.status == 'Completed').count()
            rejected_requests = db.query(BloodRequest).filter(BloodRequest.status == 'Rejected').count()
            total_requests = db.query(BloodRequest).count()

            total_donations = db.query(BloodDonation).count()
            total_issues = db.query(BloodIssue).count()

            # Stock breakdown per blood group
            blood_groups = db.query(BloodGroup).order_by(BloodGroup.id.asc()).all()
            stock_breakdown = []
            for bg in blood_groups:
                inv = bg.inventory
                units = inv.units_available if inv else 0
                threshold = inv.low_stock_threshold if inv else 5
                stock_breakdown.append({
                    'blood_group_id': bg.id,
                    'group_name': bg.group_name,
                    'units': units,
                    'ml': inv.total_ml if inv else 0.0,
                    'threshold': threshold,
                    'is_low_stock': units <= threshold
                })

            # Recent 5 donations
            recent_donations = db.query(BloodDonation).order_by(BloodDonation.donation_date.desc(), BloodDonation.id.desc()).limit(5).all()

            # Recent 5 requests
            recent_requests = db.query(BloodRequest).order_by(BloodRequest.created_at.desc()).limit(5).all()

            return {
                'success': True,
                'stats': {
                    'total_stock_units': total_stock_units,
                    'total_stock_ml': total_stock_ml,
                    'low_stock_groups': low_stock_groups,
                    'total_donors': total_donors,
                    'total_patients': total_patients,
                    'total_hospitals': total_hospitals,
                    'total_users': total_users,
                    'total_donations': total_donations,
                    'total_issues': total_issues,
                    'pending_requests': pending_requests,
                    'approved_requests': approved_requests,
                    'completed_requests': completed_requests,
                    'rejected_requests': rejected_requests,
                    'total_requests': total_requests
                },
                'stock_breakdown': stock_breakdown,
                'recent_donations': [d.to_dict() for d in recent_donations],
                'recent_requests': [r.to_dict() for r in recent_requests]
            }, 200

    @staticmethod
    def get_donor_report():
        with get_db() as db:
            donors = db.query(Donor).all()
            total_donors = len(donors)
            eligible_count = sum(1 for d in donors if d.status == 'Eligible')
            ineligible_count = sum(1 for d in donors if d.status != 'Eligible')

            bg_distribution = {}
            gender_distribution = {'Male': 0, 'Female': 0, 'Other': 0}

            for d in donors:
                bg_name = d.blood_group.group_name if d.blood_group else 'Unknown'
                bg_distribution[bg_name] = bg_distribution.get(bg_name, 0) + 1
                g = d.gender if d.gender in gender_distribution else 'Other'
                gender_distribution[g] = gender_distribution.get(g, 0) + 1

            return {
                'success': True,
                'report_title': 'Donor Summary Report',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_donors': total_donors,
                'eligible_count': eligible_count,
                'ineligible_count': ineligible_count,
                'blood_group_distribution': bg_distribution,
                'gender_distribution': gender_distribution,
                'donors': [d.to_dict() for d in donors]
            }, 200

    @staticmethod
    def get_patient_report():
        with get_db() as db:
            patients = db.query(Patient).all()
            total_patients = len(patients)

            bg_distribution = {}
            hospital_distribution = {}

            for p in patients:
                bg_name = p.blood_group.group_name if p.blood_group else 'Unknown'
                bg_distribution[bg_name] = bg_distribution.get(bg_name, 0) + 1
                hosp = p.hospital.name if p.hospital else 'Direct Walk-in'
                hospital_distribution[hosp] = hospital_distribution.get(hosp, 0) + 1

            return {
                'success': True,
                'report_title': 'Patient Summary Report',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_patients': total_patients,
                'blood_group_distribution': bg_distribution,
                'hospital_distribution': hospital_distribution,
                'patients': [p.to_dict() for p in patients]
            }, 200

    @staticmethod
    def get_donation_report(days=30):
        with get_db() as db:
            since_date = date.today() - timedelta(days=days)
            donations = db.query(BloodDonation).filter(BloodDonation.donation_date >= since_date).order_by(BloodDonation.donation_date.desc()).all()

            total_units = sum(d.quantity_units for d in donations)
            total_ml = sum(d.quantity_ml for d in donations)

            bg_breakdown = {}
            for d in donations:
                bg_name = d.blood_group.group_name if d.blood_group else 'Unknown'
                bg_breakdown[bg_name] = bg_breakdown.get(bg_name, 0) + d.quantity_units

            return {
                'success': True,
                'report_title': f'Donation Report (Past {days} Days)',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'period_days': days,
                'total_records': len(donations),
                'total_units_collected': total_units,
                'total_volume_ml': total_ml,
                'blood_group_units': bg_breakdown,
                'donations': [d.to_dict() for d in donations]
            }, 200

    @staticmethod
    def get_stock_report():
        with get_db() as db:
            inventories = db.query(BloodInventory).join(BloodGroup).order_by(BloodGroup.id.asc()).all()
            total_units = sum(inv.units_available for inv in inventories)
            total_ml = sum(inv.total_ml for inv in inventories)
            low_stock_items = [inv.to_dict() for inv in inventories if inv.units_available <= inv.low_stock_threshold]

            return {
                'success': True,
                'report_title': 'Blood Inventory Stock Snapshot',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_units': total_units,
                'total_volume_ml': total_ml,
                'low_stock_count': len(low_stock_items),
                'low_stock_alerts': low_stock_items,
                'inventory_snapshot': [inv.to_dict() for inv in inventories]
            }, 200

    @staticmethod
    def get_request_report():
        with get_db() as db:
            requests = db.query(BloodRequest).order_by(BloodRequest.created_at.desc()).all()
            total_requests = len(requests)
            status_counts = {'Pending': 0, 'Approved': 0, 'Rejected': 0, 'Completed': 0, 'Cancelled': 0}
            urgency_counts = {'Normal': 0, 'Urgent': 0, 'Critical': 0}

            for r in requests:
                s = r.status if r.status in status_counts else 'Pending'
                status_counts[s] = status_counts.get(s, 0) + 1
                u = r.urgency if r.urgency in urgency_counts else 'Normal'
                urgency_counts[u] = urgency_counts.get(u, 0) + 1

            return {
                'success': True,
                'report_title': 'Blood Request Report',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_requests': total_requests,
                'status_distribution': status_counts,
                'urgency_distribution': urgency_counts,
                'requests': [r.to_dict() for r in requests]
            }, 200

    @staticmethod
    def get_issue_report():
        with get_db() as db:
            issues = db.query(BloodIssue).order_by(BloodIssue.issue_date.desc()).all()
            total_issued_records = len(issues)
            total_issued_units = sum(i.quantity_units for i in issues)

            bg_counts = {}
            for i in issues:
                bg = i.blood_group.group_name if i.blood_group else 'Unknown'
                bg_counts[bg] = bg_counts.get(bg, 0) + i.quantity_units

            return {
                'success': True,
                'report_title': 'Blood Issue & Fulfillment Report',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_records': total_issued_records,
                'total_units_issued': total_issued_units,
                'units_by_blood_group': bg_counts,
                'issues': [i.to_dict() for i in issues]
            }, 200
