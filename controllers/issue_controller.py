import uuid
from datetime import datetime, timezone
from database import get_db
from models import BloodIssue, BloodRequest, BloodInventory, HospitalInventory, BloodGroup
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
    def issue_blood(data, issued_by='BloodBank Staff'):
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

            # Check central stock inventory
            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == req.blood_group_id).first()
            bg_name = req.blood_group.group_name if req.blood_group else 'Blood'

            if not inv or inv.units_available < quantity_to_issue:
                available = inv.units_available if inv else 0
                return {
                    'success': False,
                    'message': f'Insufficient stock in Blood Bank for {bg_name}. Required: {quantity_to_issue} units, Available: {available} units.'
                }, 400

            # 1. Deduct Central Blood Bank Inventory
            inv.units_available -= quantity_to_issue
            inv.total_ml = max(0.0, inv.total_ml - (float(quantity_to_issue) * 450.0))
            inv.last_updated = datetime.now(timezone.utc)

            # 2. If requested by a Hospital, credit the Hospital's own inventory
            if req.hospital_id:
                hosp_inv = db.query(HospitalInventory).filter(
                    HospitalInventory.hospital_id == req.hospital_id,
                    HospitalInventory.blood_group_id == req.blood_group_id
                ).first()
                if hosp_inv:
                    hosp_inv.units_available += quantity_to_issue
                    hosp_inv.total_ml += float(quantity_to_issue) * 450.0
                    hosp_inv.last_updated = datetime.now(timezone.utc)
                else:
                    hosp_inv = HospitalInventory(
                        hospital_id=req.hospital_id,
                        blood_group_id=req.blood_group_id,
                        units_available=quantity_to_issue,
                        total_ml=float(quantity_to_issue) * 450.0,
                        low_stock_threshold=3
                    )
                    db.add(hosp_inv)

            # 3. Update Request status to Completed
            req.status = 'Completed'
            req.updated_at = datetime.now(timezone.utc)

            # 4. Create Issue Record & Certificate
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

            # 5. Low Stock Alert Check after deduction
            if inv.units_available <= inv.low_stock_threshold:
                create_notification(
                    db,
                    title=f"⚠️ Central Blood Bank Low Stock Alert: {bg_name} ({inv.units_available} Units Left)",
                    message=f"After issuing {quantity_to_issue} unit(s) for {req.request_code}, {bg_name} stock is at or below threshold ({inv.units_available}/{inv.low_stock_threshold}).",
                    notification_type="low_stock"
                )

            # 6. Success Notification
            p_name = req.patient_name or (req.patient.name if req.patient else (req.user.name if req.user else 'Recipient'))
            create_notification(
                db,
                title=f"📦 Blood Issued: {issue_code} ({quantity_to_issue} Units {bg_name})",
                message=f"Issued {quantity_to_issue} unit(s) of {bg_name} for {p_name} to recipient {recipient_name}. Certificate: {cert_no}",
                notification_type="approval"
            )

            # 7. Audit Log
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
