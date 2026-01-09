from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from accounts.models import AccountProfile
from accounts.permissions import IsAdminRole, IsApprovedCoach
from availability.models import PlayerAvailability
from organizations.models import Association, Team, TeamCoach
from regions.models import Region


User = get_user_model()


class AccountProfileTests(TestCase):
    def test_profile_created_for_new_user(self):
        user = User.objects.create_user(username="player1", password="testpass")
        self.assertTrue(AccountProfile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.role, AccountProfile.Roles.PLAYER)

    def test_is_approved_coach_permission_fails_when_unapproved(self):
        user = User.objects.create_user(username="coach1", password="testpass")
        user.profile.role = AccountProfile.Roles.COACH
        user.profile.is_coach_approved = False
        user.profile.save()

        request = APIRequestFactory().get("/")
        request.user = user

        self.assertFalse(IsApprovedCoach().has_permission(request, None))

    def test_staff_user_is_admin_role(self):
        user = User.objects.create_user(username="admin1", password="testpass", is_staff=True)
        request = APIRequestFactory().get("/")
        request.user = user
        self.assertTrue(IsAdminRole().has_permission(request, None))


class WebRoleGuardTests(TestCase):
    def setUp(self):
        self.player = User.objects.create_user(username="player1", password="testpass")
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

    def test_player_blocked_from_coach_pages(self):
        self.client.login(username="player1", password="testpass")
        response = self.client.get("/coach/teams/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)

    def test_coach_blocked_from_player_pages(self):
        self.client.login(username="coach1", password="testpass")
        response = self.client.get("/player/profile/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)

    def test_open_players_respects_allow_list(self):
        other_player = User.objects.create_user(username="player2", password="testpass")
        other_player.profile.role = AccountProfile.Roles.PLAYER
        other_player.profile.save()

        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_teams.add(self.team_bc)
        PlayerAvailability.objects.create(player=other_player, region=self.bc, is_open=True)

        self.client.login(username="coach1", password="testpass")
        response = self.client.get("/coach/open-players/", HTTP_HOST="bc.localhost:8000")
        self.assertContains(response, "player1")
        self.assertNotContains(response, "player2")

    def test_coach_cannot_request_unassigned_team(self):
        other_team = Team.objects.create(
            region=self.bc,
            association=self.assoc_bc,
            name="Other Team",
            age_group="13U",
        )
        availability = PlayerAvailability.objects.create(player=self.player, region=self.bc, is_open=True)
        availability.allowed_teams.add(self.team_bc)

        self.client.login(username="coach1", password="testpass")
        response = self.client.post(
            "/coach/requests/new/",
            {"player": str(self.player.id), "requesting_team": other_team.id, "message": "Hi"},
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice", status_code=200)

    def test_cross_region_access_blocked(self):
        assoc_on = Association.objects.create(region=self.on, name="ON Assoc")
        team_on = Team.objects.create(region=self.on, association=assoc_on, name="ON Team", age_group="13U")
        availability = PlayerAvailability.objects.create(player=self.player, region=self.on, is_open=True)
        availability.allowed_teams.add(team_on)

        self.client.login(username="coach1", password="testpass")
        response = self.client.get(f"/coach/open-players/{self.player.id}/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 404)
