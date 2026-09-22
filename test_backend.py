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
        return data['token']

    def test_01_root_and_health_status(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        
        health_resp = self.client.get('/health')
        self.assertEqual(health_resp.status_code, 200)
        data = json.loads(health_resp.data)
        self.assertEqual(data['status'], 'OK')
        print("✓ Test 01: System Status & Health Endpoint Passed")

    def test_02_auth_flows(self):
        # 1. Invalid Login
        resp = self.client.post('/api/auth/login', data=json.dumps({
            'email': 'invalid@bloodbank.com',
            'password': 'wrong'
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

        # 2. Valid Login
        token = self.login_as('admin@bloodbank.com', 'Admin@123')
        self.assertTrue(bool(token))

        # 3. Get Current User (Me)
        me_resp = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(me_resp.status_code, 200)
        me_data = json.loads(me_resp.data)
        self.assertEqual(me_data['user']['email'], 'admin@bloodbank.com')

        # 4. Forgot Password & Reset
        fp_resp = self.client.post('/api/auth/forgot-password', data=json.dumps({
            'email': 'staff@bloodbank.com'
        }), content_type='application/json')
        self.assertEqual(fp_resp.status_code, 200)
        print("✓ Test 02: Auth & Role Verification Passed")

    def test_03_blood_groups_and_inventory(self):
        token = self.login_as('admin@bloodbank.com', 'Admin@123')
        headers = {'Authorization': f'Bearer {token}'}

        # 1. Blood groups list
        bg_resp = self.client.get('/api/blood-groups', headers=headers)
        self.assertEqual(bg_resp.status_code, 200)
        bg_data = json.loads(bg_resp.data)
        self.assertEqual(len(bg_data['blood_groups']), 8)

        # 2. Inventory list
        inv_resp = self.client.get('/api/inventory', headers=headers)
        self.assertEqual(inv_resp.status_code, 200)
        inv_data = json.loads(inv_resp.data)
        self.assertGreater(inv_data['total_units'], 0)
        print("✓ Test 03: Blood Groups (8 Standard) & Inventory Passed")

    def test_04_end_to_end_donation_to_issue_flow(self):
        """
        Comprehensive End-to-End Test:
        1. Query initial stock for O+
        2. Register Donor -> Add Donation (+2 units)
        3. Verify Stock incremented (+2 units)
        4. Create Patient Blood Request (2 units)
        5. Approve Request
        6. Issue Blood (-2 units)
        7. Verify Stock decremented (-2 units)
        8. Verify Certificate generation & reports
        """
        token = self.login_as('admin@bloodbank.com', 'Admin@123')
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # Step 1: Initial inventory of O+
        inv_before = json.loads(self.client.get('/api/inventory', headers=headers).data)
        o_pos_inv_before = next(i for i in inv_before['inventory'] if i['blood_group_name'] == 'O+')
        initial_units = o_pos_inv_before['units_available']
        bg_id = o_pos_inv_before['blood_group_id']

        # Step 2: Register a new donor
        donor_resp = self.client.post('/api/donors', headers=headers, data=json.dumps({
            'name': 'Automated Test Donor',
            'age': 30,
            'gender': 'Male',
            'blood_group_id': bg_id,
            'contact': '+1-555-9999',
            'email': 'donor.test@bloodbank.com',
            'address': 'Lab 101, Metro City',
            'status': 'Eligible'
        }))
        self.assertEqual(donor_resp.status_code, 201)
        donor_id = json.loads(donor_resp.data)['donor']['id']

        # Step 3: Register a Donation of 2 units
        don_resp = self.client.post('/api/donations', headers=headers, data=json.dumps({
            'donor_id': donor_id,
            'blood_group_id': bg_id,
            'quantity_units': 2,
            'quantity_ml': 900.0,
            'blood_pressure': '120/80',
            'hemoglobin': 14.5
        }))
        self.assertEqual(don_resp.status_code, 201)

        # Step 4: Verify inventory increment
        inv_after_don = json.loads(self.client.get('/api/inventory', headers=headers).data)
        o_pos_after_don = next(i for i in inv_after_don['inventory'] if i['blood_group_name'] == 'O+')
        self.assertEqual(o_pos_after_don['units_available'], initial_units + 2)

        # Step 5: Register a Patient
        patient_resp = self.client.post('/api/patients', headers=headers, data=json.dumps({
            'name': 'Automated Test Patient',
            'age': 40,
            'gender': 'Female',
            'blood_group_id': bg_id,
            'condition': 'Post-Op Transfusion',
            'contact': '+1-555-8888',
            'status': 'Admitted'
        }))
        self.assertEqual(patient_resp.status_code, 201)
        patient_id = json.loads(patient_resp.data)['patient']['id']

        # Step 6: Create Blood Request (2 units)
        req_resp = self.client.post('/api/requests', headers=headers, data=json.dumps({
            'patient_id': patient_id,
            'blood_group_id': bg_id,
            'quantity_units': 2,
            'urgency': 'Urgent',
            'reason': 'Emergency Transfusion'
        }))
        self.assertEqual(req_resp.status_code, 201)
        req_id = json.loads(req_resp.data)['request']['id']

        # Step 7: Approve Request
        appr_resp = self.client.put(f'/api/requests/{req_id}/status', headers=headers, data=json.dumps({
            'status': 'Approved'
        }))
        self.assertEqual(appr_resp.status_code, 200)

        # Step 8: Issue Blood
        issue_resp = self.client.post('/api/issues', headers=headers, data=json.dumps({
            'request_id': req_id,
            'quantity_units': 2,
            'recipient_name': 'Nurse Jennifer',
            'recipient_contact': '+1-555-7777',
            'remarks': 'Issued to ICU Floor 3'
        }))
        self.assertEqual(issue_resp.status_code, 201)
        issue_data = json.loads(issue_resp.data)
        self.assertTrue('certificate_no' in issue_data['issue'])

        # Step 9: Verify inventory decrement back to initial
        inv_after_issue = json.loads(self.client.get('/api/inventory', headers=headers).data)
        o_pos_after_issue = next(i for i in inv_after_issue['inventory'] if i['blood_group_name'] == 'O+')
        self.assertEqual(o_pos_after_issue['units_available'], initial_units)

        # Step 10: Verify Search & Reports
        search_resp = self.client.get('/api/search/blood?blood_group=O+', headers=headers)
        self.assertEqual(search_resp.status_code, 200)

        report_resp = self.client.get('/api/reports/dashboard-summary', headers=headers)
        self.assertEqual(report_resp.status_code, 200)
        print("✓ Test 04: Complete End-to-End Lifecycle Passed (Donation -> Stock + -> Request -> Issue -> Stock -)")

if __name__ == '__main__':
    unittest.main()
