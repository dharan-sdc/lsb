import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
import unittest
import json

class BloodBankTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def login_as(self, email, password):
        resp = self.client.post('/api/auth/login', data=json.dumps({
            'email': email,
            'password': password
        }), content_type='application/json')
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200, f"Login failed for {email}: {data}")
        return data['token'], data['user']

    def test_01_root_and_health_status(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        
        health_resp = self.client.get('/health')
        self.assertEqual(health_resp.status_code, 200)
        data = json.loads(health_resp.data)
        self.assertEqual(data['status'], 'OK')
        print("✓ Test 01: System Status & Health Endpoint Passed")

    def test_02_four_role_authentications(self):
        # 1. Admin Login
        admin_token, admin_user = self.login_as('admin@bloodbank.com', 'Admin@123')
        self.assertEqual(admin_user['role'], 'Admin')

        # 2. BloodBank Login
        bb_token, bb_user = self.login_as('bloodbank@bloodbank.com', 'Bank@123')
        self.assertEqual(bb_user['role'], 'BloodBank')

        # 3. Hospital Login
        hosp_token, hosp_user = self.login_as('hospital@bloodbank.com', 'Hospital@123')
        self.assertEqual(hosp_user['role'], 'Hospital')

        # 4. User Login (Donor + Seeker)
        user_token, usr = self.login_as('user@bloodbank.com', 'User@123')
        self.assertEqual(usr['role'], 'User')
        self.assertEqual(usr['blood_group_name'], 'O+')

        print("✓ Test 02: 4 Primary Role Authentications Passed (Admin, BloodBank, Hospital, User)")

    def test_03_user_role_donor_and_seeker_flow(self):
        """
        User role can:
        - Self-donate blood (increases central inventory)
        - View my-donations
        - Create a blood request for themselves or family
        - View my-requests
        """
        user_token, user_data = self.login_as('user@bloodbank.com', 'User@123')
        headers = {'Authorization': f'Bearer {user_token}', 'Content-Type': 'application/json'}
        target_bg_id = user_data.get('blood_group_id')

        # 1. User donates blood (1 unit)
        don_resp = self.client.post('/api/donations', headers=headers, data=json.dumps({
            'blood_group_id': target_bg_id,
            'quantity_units': 1,
            'blood_pressure': '120/80',
            'hemoglobin': 14.2
        }))
        self.assertEqual(don_resp.status_code, 201)

        # 2. Check My Donations
        my_don_resp = self.client.get('/api/donations/my-donations', headers=headers)
        self.assertEqual(my_don_resp.status_code, 200)
        my_don_data = json.loads(my_don_resp.data)
        self.assertGreaterEqual(my_don_data['count'], 1)

        # 3. User creates a blood request
        req_resp = self.client.post('/api/requests', headers=headers, data=json.dumps({
            'blood_group_id': target_bg_id,
            'quantity_units': 1,
            'urgency': 'Normal',
            'reason': 'Outpatient transfusion requirement'
        }))
        self.assertEqual(req_resp.status_code, 201)

        # 4. Check My Requests
        my_req_resp = self.client.get('/api/requests/my-requests', headers=headers)
        self.assertEqual(my_req_resp.status_code, 200)
        my_req_data = json.loads(my_req_resp.data)
        self.assertGreaterEqual(my_req_data['count'], 1)

        print("✓ Test 03: User Dual-Capability Flow Passed (User as Donor & User as Blood Seeker)")

    def test_04_hospital_role_and_hospital_inventory(self):
        """
        Hospital role can:
        - View own hospital inventory
        - Adjust hospital stock units
        - Create a batch request to Blood Bank
        - Issue blood from hospital inventory for hospital patient
        """
        hosp_token, hosp_user = self.login_as('hospital@bloodbank.com', 'Hospital@123')
        headers = {'Authorization': f'Bearer {hosp_token}', 'Content-Type': 'application/json'}

        # 1. View Hospital Inventory
        h_inv_resp = self.client.get('/api/hospital-inventory', headers=headers)
        self.assertEqual(h_inv_resp.status_code, 200)
        h_inv_data = json.loads(h_inv_resp.data)
        self.assertEqual(len(h_inv_data['inventory']), 8)
        target_bg_id = h_inv_data['inventory'][0]['blood_group_id']

        # 2. Adjust Hospital Stock (e.g. Add 2 units)
        adjust_resp = self.client.post('/api/hospital-inventory/adjust', headers=headers, data=json.dumps({
            'blood_group_id': target_bg_id,
            'units': 2,
            'action': 'add'
        }))
        self.assertEqual(adjust_resp.status_code, 200)

        # 3. Create Hospital Blood Request to Central Blood Bank
        req_resp = self.client.post('/api/requests', headers=headers, data=json.dumps({
            'blood_group_id': target_bg_id,
            'quantity_units': 3,
            'urgency': 'Urgent',
            'reason': 'Hospital Emergency Ward Surgical Stock'
        }))
        self.assertEqual(req_resp.status_code, 201)

        # 4. Issue blood from Hospital Inventory directly to Hospital Patient
        issue_pat_resp = self.client.post('/api/hospital-inventory/issue', headers=headers, data=json.dumps({
            'blood_group_id': target_bg_id,
            'units': 1,
            'patient_name': 'In-Patient Johnathan',
            'condition': 'Post-Op Knee Surgery'
        }))
        self.assertEqual(issue_pat_resp.status_code, 200)

        print("✓ Test 04: Hospital Capabilities Passed (Hospital Inventory, Stock Adjust, Request, Patient Issue)")

    def test_05_bloodbank_and_admin_operations(self):
        """
        Blood Bank & Admin:
        - View central stock
        - Approve user/hospital requests
        - Issue blood with unique certificate
        - View audit logs & user management
        """
        bb_token, _ = self.login_as('bloodbank@bloodbank.com', 'Bank@123')
        bb_headers = {'Authorization': f'Bearer {bb_token}', 'Content-Type': 'application/json'}

        admin_token, _ = self.login_as('admin@bloodbank.com', 'Admin@123')
        admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}

        # 1. Admin lists users across 4 roles
        users_resp = self.client.get('/api/admin/users', headers=admin_headers)
        self.assertEqual(users_resp.status_code, 200)
        users_list = json.loads(users_resp.data)['users']
        roles_present = {u['role'] for u in users_list}
        self.assertTrue({'Admin', 'BloodBank', 'Hospital', 'User'}.issubset(roles_present))

        # 2. Blood Bank views pending requests and approves one
        reqs_resp = self.client.get('/api/requests?status=Pending', headers=bb_headers)
        self.assertEqual(reqs_resp.status_code, 200)
        reqs = json.loads(reqs_resp.data)['requests']

        if reqs:
            req_id = reqs[0]['id']
            # Approve
            appr = self.client.put(f'/api/requests/{req_id}/status', headers=bb_headers, data=json.dumps({
                'status': 'Approved'
            }))
            self.assertEqual(appr.status_code, 200)

            # Issue
            issue_resp = self.client.post('/api/issues', headers=bb_headers, data=json.dumps({
                'request_id': req_id,
                'quantity_units': 1,
                'recipient_name': 'Authorized Representative',
                'recipient_contact': '+1-555-4444',
                'remarks': 'Issued to authorized representative'
            }))
            self.assertEqual(issue_resp.status_code, 201)
            issue_data = json.loads(issue_resp.data)
            self.assertTrue(issue_data['issue']['certificate_no'].startswith('CERT-BB-'))

        print("✓ Test 05: Blood Bank & Admin Operations Passed (Role checks, Request Approval, Central Blood Issue)")

if __name__ == '__main__':
    unittest.main()
