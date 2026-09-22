import uuid
from datetime import datetime, timezone, date
from database import get_db
from models import BloodRequest, Patient, Hospital, BloodGroup, BloodInventory, User
from auth_utils import log_audit, create_notification

class RequestController:
    @staticmethod
    def list_requests(user_id=None, hospital_id=None, requester_type=None, status=None, urgency=None, blood_group_id=None):
        with get_db() as db:
            query = db.query(BloodRequest)
            if user_id:
                try:
                    query = query.filter(BloodRequest.user_id == int(user_id))
                except ValueError:
                    pass
            if hospital_id:
                try:
                    query = query.filter(BloodRequest.hospital_id == int(hospital_id))
                except ValueError:
                    pass
            if requester_type:
                query = query.filter(BloodRequest.requester_type == requester_type)
            if status and status != 'All':
                query = query.filter(BloodRequest.status == status)
            if urgency:
                query = query.filter(BloodRequest.urgency == urgency)
            if blood_group_id:
                try:
                    query = query.filter(BloodRequest.blood_group_id == int(blood_group_id))
                except ValueError:
                    pass

            requests = query.order_by(BloodRequest.created_at.desc()).all()
            return {
                'success': True,
                'count': len(requests),
                'requests': [r.to_dict() for r in requests]
            }, 200

    @staticmethod
    def create_request(data, user_id=None, hospital_id=None, requester_type='User', requested_by='User'):
        blood_group_id = data.get('blood_group_id')
        quantity_units = data.get('quantity_units', 1)
        urgency = data.get('urgency', 'Normal')
        required_date_str = data.get('required_date')
        reason = data.get('reason', '')
        patient_name = (data.get('patient_name') or '').strip()
        patient_age = data.get('patient_age')
        patient_gender = data.get('patient_gender')
        patient_id = data.get('patient_id')
        hosp_id = data.get('hospital_id') or hospital_id
        u_id = data.get('user_id') or user_id

        if not blood_group_id:
            return {'success': False, 'message': 'Blood Group is required'}, 400

        try:
            blood_group_id = int(blood_group_id)
            quantity_units = int(quantity_units)
            if quantity_units <= 0:
                return {'success': False, 'message': 'Quantity must be at least 1 unit'}, 400
            if hosp_id:
                hosp_id = int(hosp_id)
            if u_id:
                u_id = int(u_id)
            if patient_id:
                patient_id = int(patient_id)
            if patient_age:
                patient_age = int(patient_age)
        except ValueError:
            return {'success': False, 'message': 'Invalid number format in request fields'}, 400

        required_date = date.today()
        if required_date_str:
            try:
                required_date = datetime.strptime(required_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == blood_group_id).first()
            if not bg:
                return {'success': False, 'message': 'Blood group not found'}, 404

            # Resolve patient name and requester details
            resolved_patient_name = patient_name
            if not resolved_patient_name and patient_id:
                pat = db.query(Patient).filter(Patient.id == patient_id).first()
                if pat:
                    resolved_patient_name = pat.name
                    if not patient_age:
                        patient_age = pat.age
                    if not patient_gender:
                        patient_gender = pat.gender

            if not resolved_patient_name and u_id:
                usr = db.query(User).filter(User.id == u_id).first()
                if usr:
                    resolved_patient_name = usr.name
                    if not patient_age:
                        patient_age = usr.age
                    if not patient_gender:
                        patient_gender = usr.gender

            if not resolved_patient_name:
                resolved_patient_name = f'Patient ({requested_by})'

            hosp_name = 'Direct User Request'
            if hosp_id:
                hosp = db.query(Hospital).filter(Hospital.id == hosp_id).first()
                if hosp:
                    hosp_name = hosp.name

            unique_suffix = str(uuid.uuid4())[:8].upper()
            request_code = f"REQ-{datetime.now().strftime('%Y%m%d')}-{unique_suffix}"

            req = BloodRequest(
                request_code=request_code,
                requester_type=requester_type,
                user_id=u_id,
                patient_id=patient_id,
                patient_name=resolved_patient_name,
                patient_age=patient_age,
                patient_gender=patient_gender,
                hospital_id=hosp_id,
                blood_group_id=blood_group_id,
                quantity_units=quantity_units,
                urgency=urgency,
                required_date=required_date,
                reason=reason,
                status='Pending',
                requested_by=requested_by
            )
            db.add(req)

            # Notification
            urgency_icon = '🚨' if urgency == 'Critical' else ('⚡' if urgency == 'Urgent' else '📋')
            create_notification(
                db,
                title=f"{urgency_icon} New Blood Request: {bg.group_name} ({quantity_units} Units)",
                message=f"Request {request_code} for {resolved_patient_name} ({hosp_name}) - Urgency: {urgency}",
                notification_type="request_alert"
            )

            log_audit(db, 'REQUEST_CREATED', 'BloodRequest', f'Created blood request {request_code} for {resolved_patient_name} ({hosp_name})')
            db.commit()

            return {
                'success': True,
                'message': f'Blood request {request_code} created successfully and sent to Blood Bank for approval',
                'request': req.to_dict()
            }, 201

    @staticmethod
    def get_request(request_id):
        with get_db() as db:
            req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
            if not req:
                return {'success': False, 'message': 'Blood request not found'}, 404

            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == req.blood_group_id).first()
            units_in_stock = inv.units_available if inv else 0

            req_dict = req.to_dict()
            req_dict['stock_available'] = units_in_stock
            req_dict['is_stock_sufficient'] = units_in_stock >= req.quantity_units

            return {'success': True, 'request': req_dict}, 200

    @staticmethod
    def update_status(request_id, new_status, rejection_reason=None):
        if new_status not in ['Pending', 'Approved', 'Rejected', 'Completed', 'Cancelled']:
            return {'success': False, 'message': 'Invalid status option'}, 400

        with get_db() as db:
            req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
            if not req:
                return {'success': False, 'message': 'Request not found'}, 404

            req.status = new_status
            if rejection_reason:
                req.rejection_reason = rejection_reason
            req.updated_at = datetime.now(timezone.utc)

            bg_name = req.blood_group.group_name if req.blood_group else 'Blood'

            if new_status == 'Approved':
                create_notification(
                    db,
                    title=f"✅ Blood Request Approved: {req.request_code}",
                    message=f"Request for {req.quantity_units} unit(s) of {bg_name} for {req.patient_name or 'patient'} has been APPROVED. Ready for blood issuance.",
                    notification_type="approval"
                )
            elif new_status == 'Rejected':
                create_notification(
                    db,
                    title=f"❌ Blood Request Rejected: {req.request_code}",
                    message=f"Request {req.request_code} was rejected. Reason: {rejection_reason or 'Not specified'}",
                    notification_type="rejection"
                )

            log_audit(db, 'REQUEST_STATUS_UPDATED', 'BloodRequest', f'Request {req.request_code} status changed to {new_status}')
            db.commit()

            return {'success': True, 'message': f'Request status updated to {new_status}', 'request': req.to_dict()}, 200

    @staticmethod
    def delete_request(request_id):
        with get_db() as db:
            req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
            if not req:
                return {'success': False, 'message': 'Request not found'}, 404

            code = req.request_code
            db.delete(req)
            log_audit(db, 'REQUEST_DELETED', 'BloodRequest', f'Deleted blood request {code}')
            db.commit()

            return {'success': True, 'message': f'Request {code} deleted successfully'}, 200
