from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import AccountProfile


User = get_user_model()


class MeEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_me_requires_auth(self):
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_profile_and_region(self):
        user = User.objects.create_user(
            username="player1",
            password="testpass",
            email="player@example.com",
        )
        user.profile.role = AccountProfile.Roles.PLAYER
        user.profile.save()

        self.client.force_authenticate(user=user)
        response = self.client.get("/api/v1/me/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "player1")
        self.assertEqual(response.data["role"], AccountProfile.Roles.PLAYER)
        self.assertEqual(response.data["is_coach_approved"], False)
        self.assertEqual(response.data["region_code"], "bc")
