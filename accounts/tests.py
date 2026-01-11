from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from accounts.models import AccountProfile
from accounts.permissions import IsAdminRole, IsApprovedCoach
from availability.models import PlayerAvailability
from organizations.models import Association, Team, TeamCoach
from profiles.models import PlayerProfile
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


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CoachSignupTests(TestCase):
    def setUp(self):
        self.region = Region.objects.get(code="bc")
        self.assoc_match = Association.objects.create(
            region=self.region,
            name="BC Assoc",
            official_domain="vancouverminor.com",
        )
        self.assoc_nomatch = Association.objects.create(
            region=self.region,
            name="Other Assoc",
            official_domain="other.org",
        )

    def _extract_token(self, email_body):
        marker = "/signup/coach/verify/"
        start = email_body.find(marker)
        if start == -1:
            return None
        token = email_body[start + len(marker):].split()[0].strip()
        return token.strip("/")

    def test_domain_match_auto_approves_after_verification(self):
        response = self.client.post(
            "/signup/coach/",
            {
                "first_name": "Pat",
                "last_name": "Coach",
                "association": self.assoc_match.id,
                "email": "pat@vancouverminor.com",
                "phone_number": "555-0101",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="pat@vancouverminor.com")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.role, AccountProfile.Roles.COACH)
        self.assertTrue(user.profile.is_coach_approved)

        self.assertEqual(len(mail.outbox), 1)
        token = self._extract_token(mail.outbox[0].body)
        self.assertIsNotNone(token)

        self.assertFalse(self.client.login(username=user.username, password="testpass123"))
        verify_response = self.client.get(
            f"/signup/coach/verify/{token}/",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(verify_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(self.client.login(username=user.username, password="testpass123"))

    def test_domain_mismatch_requires_admin_approval(self):
        response = self.client.post(
            "/signup/coach/",
            {
                "first_name": "Alex",
                "last_name": "Coach",
                "association": self.assoc_nomatch.id,
                "email": "alex@gmail.com",
                "phone_number": "555-0202",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="alex@gmail.com")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.role, AccountProfile.Roles.COACH)
        self.assertFalse(user.profile.is_coach_approved)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PlayerSignupTests(TestCase):
    def setUp(self):
        self.region = Region.objects.get(code="bc")
        self.assoc = Association.objects.create(region=self.region, name="BC Assoc")

    def _extract_token(self, email_body):
        marker = "/signup/player/verify/"
        start = email_body.find(marker)
        if start == -1:
            return None
        token = email_body[start + len(marker):].split()[0].strip()
        return token.strip("/")

    def test_player_signup_requires_verification(self):
        response = self.client.post(
            "/signup/player/",
            {
                "first_name": "Sam",
                "last_name": "Player",
                "birth_year": 2011,
                "email": "sam@example.com",
                "phone_number": "555-0303",
                "current_association": self.assoc.id,
                "available_for_transfer": "on",
                "profile_visibility": "specific",
                "visible_associations": [self.assoc.id],
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="sam@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.role, AccountProfile.Roles.PLAYER)

        profile = PlayerProfile.objects.get(user=user)
        self.assertEqual(profile.birth_year, 2011)
        self.assertEqual(profile.profile_visibility, PlayerProfile.Visibility.SPECIFIC)
        self.assertTrue(profile.visible_associations.filter(id=self.assoc.id).exists())

        availability = PlayerAvailability.objects.get(player=user)
        self.assertTrue(availability.is_open)
        self.assertFalse(availability.is_committed)

        self.assertEqual(len(mail.outbox), 1)
        token = self._extract_token(mail.outbox[0].body)
        self.assertIsNotNone(token)

        self.assertFalse(self.client.login(username=user.username, password="testpass123"))
        verify_response = self.client.get(
            f"/signup/player/verify/{token}/",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(verify_response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(self.client.login(username=user.username, password="testpass123"))
