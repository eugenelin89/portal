from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from availability.models import PlayerAvailability
from contacts.models import AuditLog, ContactRequest
from organizations.models import Association, Team, TeamCoach
from regions.models import Region


User = get_user_model()


class ContactRequestApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.player = User.objects.create_user(
            username="player1",
            password="testpass",
            email="player1@example.com",
        )
        self.player.profile.role = AccountProfile.Roles.PLAYER
        self.player.profile.save()

        self.coach = User.objects.create_user(username="coach1", password="testpass")
        self.coach.profile.role = AccountProfile.Roles.COACH
        self.coach.profile.is_coach_approved = True
        self.coach.profile.save()

        self.bc = Region.objects.get(code="bc")
        self.on = Region.objects.create(code="on", name="Ontario", is_active=True)
        self.assoc_bc = Association.objects.create(region=self.bc, name="BC Assoc")
        self.team_bc = Team.objects.create(region=self.bc, association=self.assoc_bc, name="BC Team", age_group="13U")
        TeamCoach.objects.create(user=self.coach, team=self.team_bc, is_active=True)

    def test_non_open_player_blocked(self):
        PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=False)
        self.client.force_authenticate(user=self.coach)

        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id, "message": "Hi"},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_pending_blocked(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)

        ContactRequest.objects.create(
            player=self.player,
            requesting_team=self.team_bc,
            requested_by=self.coach,
            region=self.bc,
        )

        self.client.force_authenticate(user=self.coach)
        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 400)

    def test_permissions_and_region_isolation(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.on, is_open=True)
        assoc_on = Association.objects.create(region=self.on, name="ON Assoc")
        team_on = Team.objects.create(region=self.on, association=assoc_on, name="ON Team", age_group="13U")
        availability.allowed_associations.add(assoc_on)

        self.client.force_authenticate(user=self.coach)
        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": team_on.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 400)

    def test_unapproved_coach_cannot_create_request(self):
        unapproved = User.objects.create_user(username="coach2", password="testpass")
        unapproved.profile.role = AccountProfile.Roles.COACH
        unapproved.profile.is_coach_approved = False
        unapproved.profile.save()
        TeamCoach.objects.create(user=unapproved, team=self.team_bc, is_active=True)

        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=unapproved)
        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 403)

    def test_player_can_respond_only_own_request(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)
        contact_request = ContactRequest.objects.create(
            player=self.player,
            requesting_team=self.team_bc,
            requested_by=self.coach,
            region=self.bc,
        )

        other_player = User.objects.create_user(username="player2", password="testpass")
        other_player.profile.role = AccountProfile.Roles.PLAYER
        other_player.profile.save()

        self.client.force_authenticate(user=other_player)
        response = self.client.post(
            f"/api/v1/contact-requests/{contact_request.id}/respond/",
            {"status": "approved"},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 400)

    def test_audit_log_entries_created(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)
        self.client.force_authenticate(user=self.coach)

        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id, "message": "Hi"},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 201)
        contact_id = response.data["id"]
        self.assertTrue(AuditLog.objects.filter(action="CONTACT_REQUEST_CREATED", target_id=contact_id).exists())

        self.client.force_authenticate(user=self.player)
        response = self.client.post(
            f"/api/v1/contact-requests/{contact_id}/respond/",
            {"status": "approved"},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="CONTACT_REQUEST_APPROVED", target_id=contact_id).exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact_request_sends_email(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)
        self.client.force_authenticate(user=self.coach)

        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id, "message": "Hi"},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/player/requests/", mail.outbox[0].body)

    def test_open_players_endpoint_filters_expired(self):
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
            expires_at=timezone.now() - timedelta(days=1),
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/open-players/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_contact_request_blocked_for_committed_player(self):
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
            is_committed=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.post(
            "/api/v1/contact-requests/",
            {"player_id": self.player.id, "requesting_team_id": self.team_bc.id},
            format="json",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 400)

    def test_open_players_excludes_committed(self):
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
            is_committed=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/open-players/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_open_players_respects_allow_list(self):
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
        )
        other_assoc = Association.objects.create(region=self.bc, name="Other Assoc")
        Team.objects.create(
            region=self.bc,
            association=other_assoc,
            name="Other Team",
            age_group="13U",
        )
        availability.allowed_associations.add(other_assoc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/open-players/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_open_players_region_isolation(self):
        availability = PlayerAvailability.objects.create(
            player=self.player,
            region=self.bc,
            is_open=True,
        )
        availability.allowed_associations.add(self.assoc_bc)

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/open-players/", HTTP_HOST="on.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_contact_requests_list_region_isolation(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)
        ContactRequest.objects.create(
            player=self.player,
            requesting_team=self.team_bc,
            requested_by=self.coach,
            region=self.bc,
        )

        self.client.force_authenticate(user=self.coach)
        response = self.client.get("/api/v1/contact-requests/", HTTP_HOST="on.localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_contact_request_respond_region_isolation(self):
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_associations.add(self.assoc_bc)
        contact_request = ContactRequest.objects.create(
            player=self.player,
            requesting_team=self.team_bc,
            requested_by=self.coach,
            region=self.bc,
        )

        self.client.force_authenticate(user=self.player)
        response = self.client.post(
            f"/api/v1/contact-requests/{contact_request.id}/respond/",
            {"status": "approved"},
            format="json",
            HTTP_HOST="on.localhost:8000",
        )
        self.assertEqual(response.status_code, 404)
