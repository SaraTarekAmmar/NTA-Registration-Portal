import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth import require_editor
from main import app


app.dependency_overrides[require_editor] = lambda: {
    "email": "editor@nta.edu.eg",
    "role": "editor",
}


class TestAdmissionSteps(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _fixed_payload(self):
        return [
            {
                "step_key": "electronic_registration",
                "step_type": "electronic_registration",
                "title_ar": "Online Registration",
                "is_required": True,
                "config_json": {"fixed": True, "is_active": True, "canDelete": False, "canDisable": False},
            },
            {
                "step_key": "electronic_screening",
                "step_type": "electronic_screening",
                "title_ar": "Online Screening",
                "is_required": True,
                "config_json": {"fixed": True, "is_active": True, "canDelete": False, "canDisable": False},
            },
            {
                "step_key": "security_clearance",
                "step_type": "security_clearance",
                "title_ar": "Security Clearance",
                "is_required": True,
                "config_json": {"fixed": True, "is_active": True, "canDelete": False, "canDisable": False},
            },
            {
                "step_key": "psychometric_test",
                "step_type": "psychometric_test",
                "title_ar": "Psychometric Test",
                "is_required": True,
                "config_json": {"fixed": True, "is_active": True, "canDelete": False, "canDisable": False},
            },
            {
                "step_key": "qualifying_exams",
                "step_type": "qualifying_exams",
                "title_ar": "Qualifying Exams",
                "is_required": True,
                "config_json": {"fixed": True, "is_active": True, "canDelete": False, "canDisable": False},
            },
        ]

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_empty(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        response = self.client.get("/api/courses/1/admission-steps")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 5)

        fixed_keys = [
            "electronic_registration",
            "electronic_screening",
            "security_clearance",
            "psychometric_test",
            "qualifying_exams",
        ]
        for index, key in enumerate(fixed_keys):
            self.assertEqual(data[index]["step_key"], key)
            self.assertEqual(data[index]["step_type"], key)
            self.assertEqual(data[index]["step_order"], index)
            self.assertTrue(data[index]["config_json"]["fixed"])
            self.assertTrue(data[index]["config_json"]["is_active"])

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_repaired(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "step_key": "electronic_registration",
                "step_type": "electronic_registration",
                "title_ar": "Online Registration",
                "step_order": 0,
                "is_required": 1,
                "config_json": json.dumps({"is_active": True, "fixed": True, "canDelete": False, "canDisable": False}),
            },
            {
                "step_key": "security_clearance",
                "step_type": "security_clearance",
                "title_ar": "Security Clearance",
                "step_order": 2,
                "is_required": 1,
                "config_json": json.dumps({"is_active": True, "fixed": True, "canDelete": False, "canDisable": False}),
            },
        ]

        response = self.client.get("/api/courses/1/admission-steps")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 5)

        fixed_keys = [
            "electronic_registration",
            "electronic_screening",
            "security_clearance",
            "psychometric_test",
            "qualifying_exams",
        ]
        for index, key in enumerate(fixed_keys):
            self.assertEqual(data[index]["step_key"], key)
            self.assertEqual(data[index]["step_order"], index)

    @patch("routers.courses.get_db_connection")
    def test_get_admission_steps_with_custom(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "step_key": "electronic_registration",
                "step_type": "electronic_registration",
                "title_ar": "Online Registration",
                "step_order": 0,
                "is_required": 1,
                "config_json": "{}",
            },
            {
                "step_key": "electronic_screening",
                "step_type": "electronic_screening",
                "title_ar": "Online Screening",
                "step_order": 1,
                "is_required": 1,
                "config_json": "{}",
            },
            {
                "step_key": "custom_interview",
                "step_type": "first_interview",
                "title_ar": "First Interview",
                "step_order": 2,
                "is_required": 0,
                "config_json": "{}",
            },
            {
                "step_key": "security_clearance",
                "step_type": "security_clearance",
                "title_ar": "Security Clearance",
                "step_order": 3,
                "is_required": 1,
                "config_json": "{}",
            },
            {
                "step_key": "psychometric_test",
                "step_type": "psychometric_test",
                "title_ar": "Psychometric Test",
                "step_order": 4,
                "is_required": 1,
                "config_json": "{}",
            },
            {
                "step_key": "qualifying_exams",
                "step_type": "qualifying_exams",
                "title_ar": "Qualifying Exams",
                "step_order": 5,
                "is_required": 1,
                "config_json": "{}",
            },
        ]

        response = self.client.get("/api/courses/1/admission-steps")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 6)
        self.assertEqual(data[2]["step_key"], "custom_interview")
        self.assertEqual(data[2]["step_order"], 2)
        self.assertEqual(data[3]["step_key"], "security_clearance")
        self.assertEqual(data[3]["step_order"], 3)

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_valid(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        response = self.client.put("/api/courses/1/admission-steps", json=self._fixed_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Admission steps updated successfully")
        mock_cursor.execute.assert_any_call(
            "DELETE FROM course_steps WHERE course_id=%s AND path_type='admission'",
            (1,),
        )

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_missing_fixed(self, mock_get_db):
        payload = self._fixed_payload()[:-1]

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("qualifying_exams", response.json()["detail"])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_invalid_flags(self, mock_get_db):
        payload = self._fixed_payload()
        payload[3]["config_json"]["is_active"] = False

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("psychometric_test", response.json()["detail"])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_allows_fixed_title_edit(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        payload = self._fixed_payload()
        payload[2]["title_ar"] = "Security Review Stage"
        payload[2]["description_ar"] = "Custom editor-managed description"

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Admission steps updated successfully")
        security_insert = next(
            call
            for call in mock_cursor.execute.call_args_list
            if len(call.args) > 1 and len(call.args[1]) > 1 and call.args[1][1] == "security_clearance"
        )
        inserted_cfg = json.loads(security_insert.args[1][-1])
        self.assertEqual(inserted_cfg["description_ar"], "Custom editor-managed description")

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_first_interview_allows_dynamic_criteria(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        payload = self._fixed_payload() + [
            {
                "step_key": "first_interview_custom",
                "step_type": "first_interview",
                "title_ar": "First Interview",
                "is_required": False,
                "config_json": {
                    "enforce_mandatory": True,
                    "criteria": [
                        {"key": "appearance", "title_ar": "Appearance", "weight": 1, "scale_min": 1, "scale_max": 5},
                        {"key": "motivation_enthusiasm", "title_ar": "Motivation", "weight": 1, "scale_min": 1, "scale_max": 5},
                        {"key": "self_confidence", "title_ar": "Self Confidence", "weight": 1, "scale_min": 1, "scale_max": 5},
                        {"key": "initiative", "title_ar": "Initiative", "weight": 1, "scale_min": 1, "scale_max": 5},
                        {"key": "communication_skills", "title_ar": "Communication", "weight": 1, "scale_min": 1, "scale_max": 5},
                    ],
                },
            }
        ]

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 200)
        interview_insert = next(
            call
            for call in mock_cursor.execute.call_args_list
            if len(call.args) > 1 and len(call.args[1]) > 2 and call.args[1][2] == "first_interview"
        )
        inserted_cfg = json.loads(interview_insert.args[1][-1])
        self.assertTrue(inserted_cfg["enforce_mandatory"])
        self.assertEqual(
            [item["key"] for item in inserted_cfg["criteria"]],
            [
                "appearance",
                "motivation_enthusiasm",
                "self_confidence",
                "initiative",
                "communication_skills",
            ],
        )

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_out_of_order(self, mock_get_db):
        payload = self._fixed_payload()
        payload[1], payload[2] = payload[2], payload[1]

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("security_clearance", response.json()["detail"])

    @patch("routers.courses.get_db_connection")
    def test_put_admission_steps_registration_not_first(self, mock_get_db):
        payload = [
            {
                "step_key": "custom_first",
                "step_type": "first_interview",
                "title_ar": "First Interview",
                "is_required": False,
                "config_json": {"fixed": False, "is_active": True, "canDelete": True, "canDisable": True},
            }
        ] + self._fixed_payload()

        response = self.client.put("/api/courses/1/admission-steps", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("electronic_registration", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
