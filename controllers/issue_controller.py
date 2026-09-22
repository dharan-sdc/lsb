import uuid
from datetime import datetime, timezone
from database import get_db
from models import BloodIssue, BloodRequest, BloodInventory, BloodGroup
from auth_utils import log_audit, create_notification

class IssueController:
    @staticmethod
    def list_issues():
        with get_db() as db:
            issues = db.query(BloodIssue).order_by(BloodIssue.issue_date.desc()).all()
            return {
                'success': True,
                'count': len(issues),
                'issues': [i.to_dict() for i in issues]
            }, 200

    @staticmethod
    def issue_blood(data, issued_by='Staff'):
        request_id = data.get('request_id')
        recipient_name = (data.get('recipient_name') or '').strip()
        recipient_contact = (data.get('recipient_contact') or '').strip()
        remarks = data.get('remarks', 'Dispatched according to doctor prescription')

        if not request_id or not recipient_name:
            return {'success': False, 'message': 'Request ID and Recipient Name are required'}, 400

        try:
            request_id = int(request_id)
        except ValueError:
            return {'success': False, 'message': 'Request ID must be an integer'}, 400

        with get_db() as db:
            req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
            if not req:
                return {'success': False, 'message': 'Blood request not found'}, 404

            if req.status == 'Completed':
                return {'success': False, 'message': f'Request {req.request_code} has already been fulfilled and issued'}, 400

            if req.status == 'Rejected':
                return {'success': False, 'message': f'Cannot issue blood for a rejected request ({req.request_code})'}, 400

            quantity_to_issue = data.get('quantity_units')
            if quantity_to_issue:
                try:
                    quantity_to_issue = int(quantity_to_issue)
                except ValueError:
                    quantity_to_issue = req.quantity_units
            else:
                quantity_to_issue = req.quantity_units

            # Check stock inventory
            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == req.blood_group_id).first()
            bg_name = req.blood_group.group_name if req.blood_group else 'Blood'

            if not inv or inv.units_available < quantity_to_issue:
                available = inv.units_available if inv else 0
                return {
                    'success': False,
                    'message': f'Insufficient stock for blood group {bg_name}. Required: {quantity_to_issue} units, Available in stock: {available} units.'
                }, 400

            # 1. Deduct Inventory
            inv.units_available -= quantity_to_issue
            inv.total_ml = max(0.0, inv.total_ml - (float(quantity_to_issue) * 450.0))
            inv.last_updated = datetime.now(timezone.utc)

            # 2. Update Request status to Completed
            req.status = 'Completed'
            req.updated_at = datetime.now(timezone.utc)

            # 3. Create Issue Record & Certificate
            unique_suffix = str(uuid.uuid4())[:8].upper()
            issue_code = f"ISS-{datetime.now().strftime('%Y%m%d')}-{unique_suffix}"
            cert_no = f"CERT-BB-{datetime.now().strftime('%Y%m%d')}-{unique_suffix}"

            issue = BloodIssue(
                issue_code=issue_code,
                request_id=req.id,
                blood_group_id=req.blood_group_id,
                quantity_units=quantity_to_issue,
                issue_date=datetime.now(timezone.utc),
                issued_by=issued_by,
                recipient_name=recipient_name,
                recipient_contact=recipient_contact,
                certificate_no=cert_no,
                remarks=remarks
            )
            db.add(issue)

            # 4. Low Stock Alert Check after deduction
            if inv.units_available <= inv.low_stock_threshold:
                create_notification(
                    db,
                    title=f"⚠️ Low Stock Alert: {bg_name} ({inv.units_available} Units Left)",
                    message=f"After issuing {quantity_to_issue} unit(s) for {req.request_code}, {bg_name} stock is at or below threshold ({inv.units_available}/{inv.low_stock_threshold}).",
                    notification_type="low_stock"
                )

            # 5. Success Notification
            create_notification(
                db,
                title=f"📦 Blood Issued: {issue_code} ({quantity_to_issue} Units {bg_name})",
                message=f"Issued {quantity_to_issue} unit(s) of {bg_name} for patient {req.patient.name if req.patient else ''} to recipient {recipient_name}. Certificate: {cert_no}",
                notification_type="approval"
            )

            # 6. Audit Log
            log_audit(db, 'BLOOD_ISSUED', 'BloodIssue', f'Issued {quantity_to_issue} unit(s) {bg_name} under {issue_code} for request {req.request_code}')
            db.commit()

            return {
                'success': True,
                'message': f'Blood issued successfully! Certificate No: {cert_no}',
                'issue': issue.to_dict(),
                'remaining_stock': inv.units_available
            }, 201

    @staticmethod
    def get_issue(issue_id):
        with get_db() as db:
            issue = db.query(BloodIssue).filter(BloodIssue.id == issue_id).first()
            if not issue:
                return {'success': False, 'message': 'Blood issue record not found'}, 404
            return {'success': True, 'issue': issue.to_dict()}, 200
