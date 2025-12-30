from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from profiles.models import PlayerProfile


User = get_user_model()


class PlayerProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.player = User.objects.create_user(username="player1", password="testpass")
        self.player.profile.role = AccountProfile.Roles.PLAYER
        self.player.profile.save()

        self.coach = User.objects.create_user(username="coach1", password="testpass")
        self.coach.profile.role = AccountProfile.Roles.COACH
        self.coach.profile.save()

        self.admin = User.objects.create_user(username="admin1", password="testpass", is_staff=True)

    def test_player_can_get_and_patch_profile(self):
        self.client.force_authenticate(user=self.player)

        get_response = self.client.get("/api/v1/profile/me/")
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(PlayerProfile.objects.filter(user=self.player).exists())

        patch_response = self.client.patch(
            "/api/v1/profile/me/",
            {"display_name": "J. Player", "birth_year": 2011, "positions": ["OF"]},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["display_name"], "J. Player")

    def test_non_player_blocked(self):
        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/profile/me/")
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/api/v1/profile/me/", {"display_name": "Nope"})
        self.assertEqual(response.status_code, 403)

    def test_profile_not_listable(self):
        response = self.client.get("/api/v1/profiles/")
        self.assertEqual(response.status_code, 404)

    def test_no_other_profile_endpoint(self):
        self.client.force_authenticate(user=self.player)
        response = self.client.get("/api/v1/profile/999/")
        self.assertEqual(response.status_code, 404)
