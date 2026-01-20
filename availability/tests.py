from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from availability.models import PlayerAvailability
from contacts.models import AuditLog
from organizations.models import Association, Team, TeamCoach
from regions.models import Region


User = get_user_model()


class AvailabilityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.player = User.objects.create_user(username="player1", password="testpass")
        self.player.profile.role = AccountProfile.Roles.PLAYER
        self.player.profile.save()

        self.coach = User.objects.create_user(username="coach1", password="testpass")
        self.coach.profile.role = AccountProfile.Roles.COACH
        self.coach.profile.save()

        self.admin = User.objects.create_user(username="admin1", password="testpass", is_staff=True)

        self.bc = Region.objects.get(code="bc")
        self.on = Region.objects.create(code="on", name="Ontario", is_active=True)
        self.assoc_bc = Association.objects.create(region=self.bc, name="BC Assoc")
        self.team_bc = Team.objects.create(region=self.bc, association=self.assoc_bc, name="BC Team", age_group="13U")
        TeamCoach.objects.create(user=self.coach, team=self.team_bc, is_active=True)

    def test_player_can_toggle_open_status(self):
        self.client.force_authenticate(user=self.player)
        response = self.client.patch(
            "/api/v1/availability/me/",
            {"is_open": True},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_open"], True)

    def test_player_cannot_view_other_player_availability(self):
        other = User.objects.create_user(username="player2", password="testpass")
        other.profile.role = AccountProfile.Roles.PLAYER
        other.profile.save()
        PlayerAvailability.objects.create(player=other, region=self.bc, is_open=True)

        self.client.force_authenticate(user=self.player)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)

    def test_coach_must_be_approved_to_search(self):
        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)

    def test_approved_coach_can_search_open_players(self):
        self.coach.profile.is_coach_approved = True
        self.coach.profile.save()

        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["player_id"], self.player.id)

    def test_coach_with_profile_association_can_search_open_players(self):
        coach = User.objects.create_user(username="coach2", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.association = self.assoc_bc
        coach.profile.save()

        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_expired_availability_excluded(self):
        self.coach.profile.is_coach_approved = True
        self.coach.profile.save()

        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
            expires_at=timezone.now() - timedelta(days=1),
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_region_filtering_enforced(self):
        self.coach.profile.is_coach_approved = True
        self.coach.profile.save()

        assoc_on = Association.objects.create(region=self.on, name="ON Assoc")
        team_on = Team.objects.create(region=self.on, association=assoc_on, name="ON Team", age_group="13U")
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.on,
            is_open=True,
        )
        availability.allowed_associations.add(assoc_on)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_player_can_commit_and_is_open_forced_false(self):
        self.client.force_authenticate(user=self.player)
        response = self.client.patch(
            "/api/v1/availability/me/",
            {"is_committed": True, "is_open": True},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_committed"], True)
        self.assertEqual(response.data["is_open"], False)
        self.assertIsNotNone(response.data["committed_at"])
        self.assertTrue(
            AuditLog.objects.filter(action="COMMITTED_SET", target_type="PlayerAvailability").exists()
        )

    def test_committed_player_excluded_from_search(self):
        self.coach.profile.is_coach_approved = True
        self.coach.profile.save()

        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
            is_committed=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/search/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_player_can_manage_allowed_associations(self):
        self.client.force_authenticate(user=self.player)
        response = self.client.post(
            "/api/v1/availability/allowed-associations/",
            {"association_id": self.assoc_bc.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.assoc_bc.id)

        response = self.client.delete(
            f"/api/v1/availability/allowed-associations/{self.assoc_bc.id}/",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 204)
        response = self.client.get("/api/v1/availability/allowed-associations/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_allowed_associations_requires_player_role(self):
        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/availability/allowed-associations/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)

    def test_allowed_associations_region_isolation(self):
        self.client.force_authenticate(user=self.player)
        assoc_on = Association.objects.create(region=self.on, name="ON Assoc")
        response = self.client.post(
            "/api/v1/availability/allowed-associations/",
            {"association_id": assoc_on.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 404)
