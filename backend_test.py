#!/usr/bin/env python3
"""
SafeTrack Backend API Test Suite
Tests all core functionality including authentication, emergency alerts, and admin features
"""

import requests
import sys
import json
from datetime import datetime
import time

class SafeTrackAPITester:
    def __init__(self, base_url="https://emergency-hub-22.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.student_token = None
        self.test_student_id = f"test_student_{int(time.time())}"
        self.test_alert_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
    def make_request(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Make HTTP request and return response"""
        url = f"{self.api_url}/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response, response.status_code == expected_status
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None, False

    def test_api_status(self):
        """Test API status endpoint"""
        print("\n🔍 Testing API Status...")
        response, success = self.make_request('GET', 'status')
        
        if success and response:
            data = response.json()
            success = data.get('message') == 'SafeTrack API is running'
            details = f"Response: {data}" if not success else ""
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("API Status Check", success, details)
        return success

    def test_student_registration(self):
        """Test student registration"""
        print("\n🔍 Testing Student Registration...")
        
        student_data = {
            "name": "Test Student",
            "student_id": self.test_student_id,
            "email": f"{self.test_student_id}@test.com",
            "password": "testpass123",
            "blood_group": "A+",
            "location": "Test Campus",
            "emergency_contacts": [
                {
                    "name": "Emergency Contact",
                    "relationship": "Parent",
                    "phone": "+1234567890",
                    "email": "parent@test.com"
                }
            ]
        }
        
        response, success = self.make_request('POST', 'auth/register', student_data, expected_status=200)
        
        if success and response:
            data = response.json()
            success = data.get('data', {}).get('student_id') == self.test_student_id
            details = f"Response: {data}" if not success else ""
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Student Registration", success, details)
        return success

    def test_student_login(self):
        """Test student login"""
        print("\n🔍 Testing Student Login...")
        
        login_data = {
            "student_id": self.test_student_id,
            "password": "testpass123"
        }
        
        response, success = self.make_request('POST', 'auth/login', login_data)
        
        if success and response:
            data = response.json()
            token = data.get('access_token')
            user = data.get('user', {})
            
            if token and user.get('student_id') == self.test_student_id:
                self.student_token = token
                success = True
            else:
                success = False
                details = "Missing token or user data"
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Student Login", success, details if not success else "")
        return success

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔍 Testing Admin Login...")
        
        admin_data = {
            "student_id": "admin",
            "password": "admin123"
        }
        
        response, success = self.make_request('POST', 'auth/login', admin_data)
        
        if success and response:
            data = response.json()
            token = data.get('access_token')
            user = data.get('user', {})
            
            if token and user.get('is_admin'):
                self.admin_token = token
                success = True
            else:
                success = False
                details = "Admin user not found or not admin"
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Admin Login", success, details if not success else "")
        return success

    def test_get_student_profile(self):
        """Test getting student profile"""
        print("\n🔍 Testing Get Student Profile...")
        
        if not self.student_token:
            self.log_test("Get Student Profile", False, "No student token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.student_token}'}
        response, success = self.make_request('GET', 'students/me', headers=headers)
        
        if success and response:
            data = response.json()
            success = data.get('student_id') == self.test_student_id
            details = f"Response: {data}" if not success else ""
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Student Profile", success, details)
        return success

    def test_update_student_profile(self):
        """Test updating student profile"""
        print("\n🔍 Testing Update Student Profile...")
        
        if not self.student_token:
            self.log_test("Update Student Profile", False, "No student token available")
            return False
            
        update_data = {
            "location": "Updated Campus Location",
            "emergency_contacts": [
                {
                    "name": "Updated Emergency Contact",
                    "relationship": "Guardian",
                    "phone": "+9876543210",
                    "email": "guardian@test.com"
                }
            ]
        }
        
        headers = {'Authorization': f'Bearer {self.student_token}'}
        response, success = self.make_request('PUT', 'students/me', update_data, headers=headers)
        
        if success and response:
            data = response.json()
            success = 'message' in data
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Update Student Profile", success, details if not success else "")
        return success

    def test_create_emergency_alert(self):
        """Test creating emergency alert"""
        print("\n🔍 Testing Create Emergency Alert...")
        
        if not self.student_token:
            self.log_test("Create Emergency Alert", False, "No student token available")
            return False
            
        alert_data = {
            "message": "Test emergency situation - please help!"
        }
        
        headers = {'Authorization': f'Bearer {self.student_token}'}
        response, success = self.make_request('POST', 'alerts', alert_data, headers=headers)
        
        if success and response:
            data = response.json()
            alert_id = data.get('data', {}).get('alert_id')
            if alert_id:
                self.test_alert_id = alert_id
                success = True
            else:
                success = False
                details = "No alert ID returned"
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Create Emergency Alert", success, details if not success else "")
        return success

    def test_get_active_alerts_admin(self):
        """Test getting active alerts as admin"""
        print("\n🔍 Testing Get Active Alerts (Admin)...")
        
        if not self.admin_token:
            self.log_test("Get Active Alerts (Admin)", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response, success = self.make_request('GET', 'alerts/active', headers=headers)
        
        if success and response:
            data = response.json()
            # Should be a list of alerts
            success = isinstance(data, list)
            if success and self.test_alert_id:
                # Check if our test alert is in the list
                alert_found = any(alert.get('id') == self.test_alert_id for alert in data)
                if not alert_found:
                    success = False
                    details = "Test alert not found in active alerts"
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Active Alerts (Admin)", success, details if not success else "")
        return success

    def test_resolve_alert_admin(self):
        """Test resolving alert as admin"""
        print("\n🔍 Testing Resolve Alert (Admin)...")
        
        if not self.admin_token or not self.test_alert_id:
            self.log_test("Resolve Alert (Admin)", False, "No admin token or alert ID available")
            return False
            
        resolve_data = {
            "status": "resolved"
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response, success = self.make_request('PUT', f'alerts/{self.test_alert_id}', resolve_data, headers=headers)
        
        if success and response:
            data = response.json()
            success = 'message' in data
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Resolve Alert (Admin)", success, details if not success else "")
        return success

    def test_multilingual_support(self):
        """Test multilingual API responses"""
        print("\n🔍 Testing Multilingual Support...")
        
        # Test Bengali language parameter
        student_data = {
            "name": "Bengali Test Student",
            "student_id": f"bn_test_{int(time.time())}",
            "email": f"bn_test_{int(time.time())}@test.com",
            "password": "testpass123",
            "blood_group": "B+"
        }
        
        response, success = self.make_request('POST', 'auth/register?lang=bn', student_data)
        
        if success and response:
            data = response.json()
            # Check if response contains Bengali text
            message = data.get('message', '')
            success = 'সফলভাবে' in message or 'নিবন্ধিত' in message
            details = f"Message: {message}" if not success else ""
        else:
            success = False
            details = f"Status code: {response.status_code if response else 'No response'}"
            
        self.log_test("Multilingual Support (Bengali)", success, details)
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        print("\n🔍 Testing Unauthorized Access...")
        
        # Try to access protected endpoint without token
        response, success = self.make_request('GET', 'students/me', expected_status=401)
        
        # For this test, we expect a 401 status, so success means we got 401
        success = response and response.status_code == 401
        details = f"Status code: {response.status_code if response else 'No response'}"
        
        self.log_test("Unauthorized Access Protection", success, details if not success else "")
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting SafeTrack API Test Suite")
        print("=" * 50)
        
        # Core API tests
        self.test_api_status()
        
        # Authentication tests
        self.test_student_registration()
        self.test_student_login()
        self.test_admin_login()
        
        # Profile management tests
        self.test_get_student_profile()
        self.test_update_student_profile()
        
        # Emergency alert tests (core functionality)
        self.test_create_emergency_alert()
        self.test_get_active_alerts_admin()
        self.test_resolve_alert_admin()
        
        # Additional feature tests
        self.test_multilingual_support()
        self.test_unauthorized_access()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! SafeTrack API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Please check the issues above.")
            return 1

def main():
    """Main test runner"""
    tester = SafeTrackAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())