from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.selectors import (
    get_user_by_email,
    get_user_by_email_or_phone,
    get_user_by_phone,
)


class SelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="Teacher@StMary.ac.ke", phone="+254700000000", password="x" * 12
        )

    def test_get_user_by_email_is_case_insensitive(self):
        self.assertEqual(get_user_by_email("teacher@stmary.ac.ke"), self.user)

    def test_get_user_by_phone(self):
        self.assertEqual(get_user_by_phone("+254700000000"), self.user)

    def test_get_user_by_email_or_phone_matches_either(self):
        self.assertEqual(get_user_by_email_or_phone("teacher@stmary.ac.ke"), self.user)
        self.assertEqual(get_user_by_email_or_phone("+254700000000"), self.user)

    def test_unknown_identifier_returns_none(self):
        self.assertIsNone(get_user_by_email_or_phone("nobody@nowhere.com"))
