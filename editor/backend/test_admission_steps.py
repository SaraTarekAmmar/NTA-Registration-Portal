import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

# Ensure the editor/backend directory is on the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from core.auth import require_editor

# Override the authentication dependency so we don't need real JWT tokens
app.dependency_overrides[require_editor] = lambda: {"email": "editor@nta.edu.eg", "role": "editor"}

class TestAdmissionSteps(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_empty(self, mock_get_db):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # When database returns empty list of steps
        mock_cursor.fetchall.return_value = []
        
        response = self.client.get("/api/courses/1/admission-steps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return exactly 5 fixed default steps in order
        self.assertEqual(len(data), 5)
        fixed_keys = ['electronic_registration', 'electronic_screening', 'security_clearance', 'psychometric_test', 'qualifying_exams']
        for i, fk in enumerate(fixed_keys):
            self.assertEqual(data[i]['step_key'], fk)
            self.assertEqual(data[i]['step_type'], fk)
            self.assertEqual(data[i]['step_order'], i)
            self.assertTrue(data[i]['config_json']['fixed'])
            self.assertTrue(data[i]['config_json']['is_active'])

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_repaired(self, mock_get_db):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # DB has some old course data missing some fixed steps
        mock_cursor.fetchall.return_value = [
            {
                'step_key': 'electronic_registration',
                'step_type': 'electronic_registration',
                'title_ar': 'التسجيل الإلكتروني',
                'step_order': 0,
                'is_required': 1,
                'config_json': json.dumps({'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False})
            },
            {
                'step_key': 'security_clearance',
                'step_type': 'security_clearance',
                'title_ar': 'الاستعلام الأمني',
                'step_order': 2,
                'is_required': 1,
                'config_json': json.dumps({'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False})
            }
        ]
        
        response = self.client.get("/api/courses/1/admission-steps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should repair missing fixed steps and return all 5
        self.assertEqual(len(data), 5)
        fixed_keys = ['electronic_registration', 'electronic_screening', 'security_clearance', 'psychometric_test', 'qualifying_exams']
        for i, fk in enumerate(fixed_keys):
            self.assertEqual(data[i]['step_key'], fk)
            self.assertEqual(data[i]['step_order'], i)

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_with_custom(self, mock_get_db):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # DB has all 5 fixed steps + 1 custom step inserted between screening and security clearance
        mock_cursor.fetchall.return_value = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني', 'step_order': 0, 'is_required': 1, 'config_json': '{}'
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني', 'step_order': 1, 'is_required': 1, 'config_json': '{}'
            },
            {
                # Custom step
                'step_key': 'custom_interview', 'step_type': 'first_interview', 'title_ar': 'مقابلة أولى', 'step_order': 2, 'is_required': 0, 'config_json': '{}'
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني', 'step_order': 3, 'is_required': 1, 'config_json': '{}'
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات', 'step_order': 4, 'is_required': 1, 'config_json': '{}'
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية', 'step_order': 5, 'is_required': 1, 'config_json': '{}'
            }
        ]
        
        response = self.client.get("/api/courses/1/admission-steps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify custom step is preserved at the correct index (index 2)
        self.assertEqual(len(data), 6)
        self.assertEqual(data[2]['step_key'], 'custom_interview')
        self.assertEqual(data[2]['step_order'], 2)
        self.assertEqual(data[3]['step_key'], 'security_clearance')
        self.assertEqual(data[3]['step_order'], 3)

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_valid(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Valid payload containing all 5 fixed steps in order
        valid_payload = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=valid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Admission steps updated successfully')
        
        # Ensure DELETE and INSERT queries were called
        mock_cursor.execute.assert_any_call("DELETE FROM course_steps WHERE course_id=%s AND path_type='admission'", (1,))

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_missing_fixed(self, mock_get_db):
        # Payload missing 'qualifying_exams'
        invalid_payload = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("خطوة إجبارية مفقودة", response.json()['detail'])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_invalid_flags(self, mock_get_db):
        # Payload where psychometric_test has 'is_active: false' (disabled)
        invalid_payload = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': False, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("لا يمكن تعطيلها", response.json()['detail'])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_invalid_title(self, mock_get_db):
        # Payload where security_clearance title is changed
        invalid_payload = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'عنوان معدل غير مسموح',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("عنوان الخطوة الإجبارية", response.json()['detail'])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_out_of_order(self, mock_get_db):
        # Payload where security_clearance is placed before electronic_screening
        invalid_payload = [
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("خارج الترتيب المحدد", response.json()['detail'])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_registration_not_first(self, mock_get_db):
        # Payload where custom_step is placed at index 0
        invalid_payload = [
            {
                'step_key': 'custom_first', 'step_type': 'first_interview', 'title_ar': 'مقابلة أولى',
                'is_required': False, 'config_json': {'fixed': False, 'is_active': True, 'canDelete': True, 'canDisable': True}
            },
            {
                'step_key': 'electronic_registration', 'step_type': 'electronic_registration', 'title_ar': 'التسجيل الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening', 'step_type': 'electronic_screening', 'title_ar': 'الفرز الإلكتروني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance', 'step_type': 'security_clearance', 'title_ar': 'الاستعلام الأمني',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test', 'step_type': 'psychometric_test', 'title_ar': 'اختبار السمات',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams', 'step_type': 'qualifying_exams', 'title_ar': 'الاختبارات التأهيلية',
                'is_required': True, 'config_json': {'fixed': True, 'is_active': True, 'canDelete': False, 'canDisable': False}
            }
        ]
        
        response = self.client.put("/api/courses/1/admission-steps", json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("الخطوة الأولى يجب أن تكون التسجيل الإلكتروني", response.json()['detail'])

if __name__ == "__main__":
    unittest.main()
