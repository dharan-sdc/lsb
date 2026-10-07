from datetime import datetime, timezone, timedelta, date
import random
from database import get_db
from models import Donor, BloodGroup, BloodDonation, BloodUnit, BloodInventory, User
from auth_utils import log_audit

class ImportController:
    @staticmethod
    def preview_import(data_type, items):
        """
        Validates structure and checks duplicates before executing the import.
        data_type: 'donors', 'donations', 'units', 'inventory'
        """
        if not isinstance(items, list) or len(items) == 0:
            return {'success': False, 'message': 'No records provided to import'}, 400

        with get_db() as db:
            blood_groups = {bg.group_name.upper().strip(): bg.id for bg in db.query(BloodGroup).all()}
            validated = []
            errors = []
            duplicates = 0

            if data_type == 'donors':
                existing_emails = {d.email.lower().strip() for d in db.query(Donor.email).all() if d.email}
                existing_phones = {d.contact.strip() for d in db.query(Donor.contact).all() if d.contact}

                for idx, row in enumerate(items):
                    name = row.get('name', '').strip()
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    phone = str(row.get('phone', row.get('contact', ''))).strip()
                    email = str(row.get('email', '')).strip().lower()
                    age = row.get('age')

                    if not name:
                        errors.append(f"Row {idx+1}: Missing donor name")
                        continue

                    bg_id = blood_groups.get(bg_name, 1)
                    is_dup = (email and email in existing_emails) or (phone and phone in existing_phones)
                    if is_dup:
                        duplicates += 1

                    validated.append({
                        'index': idx + 1,
                        'name': name,
                        'blood_group': bg_name,
                        'blood_group_id': bg_id,
                        'phone': phone,
                        'contact': phone,
                        'email': email,
                        'age': age or 28,
                        'gender': row.get('gender', 'Other'),
                        'address': row.get('address', 'Migrated Donor Record'),
                        'is_duplicate': is_dup
                    })

            elif data_type == 'units':
                existing_codes = {u.unit_code.upper().strip() for u in db.query(BloodUnit.unit_code).all()}

                for idx, row in enumerate(items):
                    code = str(row.get('unit_code', '')).upper().strip()
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    bg_id = blood_groups.get(bg_name, 1)
                    status = row.get('status', 'Available')

                    if not code:
                        code = f"BU-{datetime.now(timezone.utc).year}-{random.randint(100000, 999999)}"

                    is_dup = code in existing_codes
                    if is_dup:
                        duplicates += 1

                    validated.append({
                        'index': idx + 1,
                        'unit_code': code,
                        'blood_group': bg_name,
                        'blood_group_id': bg_id,
                        'donor_name': row.get('donor_name', 'Imported Donor'),
                        'source_type': row.get('source_type', 'Existing System Import'),
                        'storage_location': row.get('storage_location', 'Main Blood Bank Fridge - Rack A'),
                        'status': status,
                        'test_status': row.get('test_status', 'Passed'),
                        'is_duplicate': is_dup
                    })

            elif data_type == 'donations':
                for idx, row in enumerate(items):
                    donor_name = row.get('donor_name', '').strip()
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    bg_id = blood_groups.get(bg_name, 1)

                    if not donor_name:
                        errors.append(f"Row {idx+1}: Missing donor name")
                        continue

                    validated.append({
                        'index': idx + 1,
                        'donor_name': donor_name,
                        'blood_group': bg_name,
                        'blood_group_id': bg_id,
                        'units': int(row.get('units', 1)),
                        'date': row.get('date', str(date.today())),
                        'status': row.get('status', 'Completed')
                    })

            return {
                'success': True,
                'data_type': data_type,
                'total_records': len(items),
                'valid_count': len(validated),
                'duplicate_count': duplicates,
                'error_count': len(errors),
                'errors': errors,
                'preview': validated[:50]  # First 50 items for preview table
            }, 200

    @staticmethod
    def execute_import(data_type, items):
        if not isinstance(items, list) or len(items) == 0:
            return {'success': False, 'message': 'No items to import'}, 400

        with get_db() as db:
            blood_groups = {bg.group_name.upper().strip(): bg.id for bg in db.query(BloodGroup).all()}
            imported_count = 0

            if data_type == 'donors':
                for row in items:
                    name = row.get('name', '').strip()
                    if not name: continue
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    bg_id = blood_groups.get(bg_name, 1)
                    contact_val = row.get('contact') or row.get('phone') or 'Not Provided'

                    d = Donor(
                        name=name,
                        blood_group_id=bg_id,
                        contact=contact_val,
                        email=row.get('email'),
                        age=int(row.get('age', 28)),
                        gender=row.get('gender', 'Other'),
                        address=row.get('address', 'Imported Donor'),
                        medical_notes='Imported via CSV/JSON migration tool',
                        status='Eligible'
                    )
                    db.add(d)
                    imported_count += 1

            elif data_type == 'units':
                today = date.today()
                for row in items:
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    bg_id = blood_groups.get(bg_name, 1)
                    code = row.get('unit_code') or f"BU-{datetime.now(timezone.utc).year}-{random.randint(100000, 999999)}"
                    status = row.get('status', 'Available')

                    u = BloodUnit(
                        unit_code=code,
                        blood_group_id=bg_id,
                        donor_name=row.get('donor_name', 'Imported Record'),
                        volume_ml=float(row.get('volume_ml', 450.0)),
                        collection_date=today - timedelta(days=2),
                        expiry_date=today + timedelta(days=40),
                        source_type='Existing System Import',
                        source_name='Migrated Inventory File',
                        storage_location=row.get('storage_location', 'Main Blood Bank Fridge - Rack A'),
                        status=status,
                        test_status=row.get('test_status', 'Passed')
                    )
                    db.add(u)
                    imported_count += 1

                    # Increment inventory if available
                    if status == 'Available':
                        inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == bg_id).first()
                        if inv:
                            inv.units_available += 1
                            inv.total_ml += 450.0

            elif data_type == 'donations':
                today = date.today()
                for row in items:
                    name = row.get('donor_name', '').strip()
                    if not name: continue
                    bg_name = str(row.get('blood_group', 'O+')).upper().strip()
                    bg_id = blood_groups.get(bg_name, 1)
                    code = f"DON-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"

                    don = BloodDonation(
                        donation_code=code,
                        donor_name=name,
                        blood_group_id=bg_id,
                        quantity_units=int(row.get('units', 1)),
                        quantity_ml=float(row.get('units', 1)) * 450.0,
                        donation_date=today,
                        status='Completed',
                        remarks='Imported from legacy blood bank dataset'
                    )
                    db.add(don)
                    imported_count += 1

            log_audit(db, 'DATA_IMPORTED', 'DataMigration', f"Imported {imported_count} {data_type} records into LSB² system")
            db.commit()

            return {
                'success': True,
                'message': f"Successfully imported {imported_count} {data_type} records into LSB² Blood Bank.",
                'imported_count': imported_count
            }, 200
