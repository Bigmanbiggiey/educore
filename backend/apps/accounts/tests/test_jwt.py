"""Sanity check that SimpleJWT (docs/authentication.md §1) actually works
against our UUID-PK custom user model. The login endpoint itself is
deferred until `permissions` exists (it must check InstitutionMembership
per docs/authentication.md §3), but this de-risks the token mechanics now.
"""

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


class SimpleJWTIntegrationTests(TestCase):
    def test_refresh_and_access_tokens_carry_the_uuid_user_id(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        self.assertEqual(str(refresh["user_id"]), str(user.id))
        self.assertEqual(access["user_id"], refresh["user_id"])
