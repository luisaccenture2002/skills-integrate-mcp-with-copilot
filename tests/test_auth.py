import json
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.routing import APIRoute

from src.app import app, require_teacher
from src.auth import (
    SESSION_TTL_SECONDS,
    TeacherCredentialsNotConfigured,
    authenticate_teacher,
    create_teacher_session,
    get_teacher_session,
    revoke_teacher_session,
    set_teacher_password,
)


class TeacherAuthenticationTests(unittest.TestCase):
    def test_passwords_are_hashed_and_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            credentials_path = Path(directory) / "teachers.json"
            password = "correct horse battery staple"

            set_teacher_password("Teacher@example.edu", password, credentials_path)

            stored_data = json.loads(credentials_path.read_text(encoding="utf-8"))
            self.assertNotIn(password, credentials_path.read_text(encoding="utf-8"))
            self.assertTrue(
                authenticate_teacher("teacher@EXAMPLE.edu", password, credentials_path)
            )
            self.assertFalse(
                authenticate_teacher(
                    "teacher@example.edu", "incorrect password", credentials_path
                )
            )
            self.assertEqual(credentials_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(stored_data["teachers"]), 1)

    def test_missing_credentials_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            credentials_path = Path(directory) / "missing.json"
            with self.assertRaises(TeacherCredentialsNotConfigured):
                authenticate_teacher("teacher", "some password", credentials_path)

    def test_sessions_expire_and_can_be_revoked(self) -> None:
        created_at = 100.0
        token = create_teacher_session("teacher", now=created_at)

        self.assertEqual(get_teacher_session(token, now=created_at + 1), "teacher")
        self.assertIsNone(
            get_teacher_session(token, now=created_at + SESSION_TTL_SECONDS)
        )

        token = create_teacher_session("teacher", now=created_at)
        revoke_teacher_session(token)
        self.assertIsNone(get_teacher_session(token, now=created_at + 1))

    def test_activity_mutations_require_teacher_authentication(self) -> None:
        routes = {
            route.path: route
            for route in app.routes
            if isinstance(route, APIRoute)
        }

        for path in (
            "/activities/{activity_name}/signup",
            "/activities/{activity_name}/unregister",
        ):
            dependencies = routes[path].dependant.dependencies
            self.assertTrue(
                any(dependency.call is require_teacher for dependency in dependencies)
            )

        self.assertFalse(routes["/activities"].dependant.dependencies)

    def test_teacher_guard_rejects_missing_session(self) -> None:
        request = type("Request", (), {"cookies": {}})()
        with self.assertRaises(HTTPException) as error:
            require_teacher(request)
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
