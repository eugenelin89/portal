from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from contacts.models import AuditLog
from organizations.models import Association, Team, TeamCoach
from regions.models import Region
from tryouts.models import TryoutEvent


User = get_user_model()


class TryoutApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_tryout(self, region, association, team=None, **kwargs):
        return TryoutEvent.objects.create(
            region=region,
            association=association,
            team=team,
            name=kwargs.get("name", "Tryout"),
            start_date=kwargs.get("start_date", date(2025, 1, 10)),
            end_date=kwargs.get("end_date", date(2025, 1, 11)),
            location=kwargs.get("location", "Field"),
            registration_url=kwargs.get("registration_url", "https://example.com"),
            is_active=kwargs.get("is_active", True),
        )

    def test_tryouts_filtered_by_region(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        assoc_on = Association.objects.create(region=on, name="ON Assoc")
        self._create_tryout(region=bc, association=assoc_bc, name="BC Tryout")
        self._create_tryout(region=on, association=assoc_on, name="ON Tryout")

        response = self.client.get("/api/v1/tryouts/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["BC Tryout"])

    def test_inactive_tryouts_excluded(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        self._create_tryout(region=bc, association=assoc_bc, name="Active")
        self._create_tryout(region=bc, association=assoc_bc, name="Inactive", is_active=False)

        response = self.client.get("/api/v1/tryouts/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["Active"])

    def test_anonymous_can_list_and_retrieve(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        tryout = self._create_tryout(region=bc, association=assoc_bc, name="Public")

        list_response = self.client.get("/api/v1/tryouts/", HTTP_HOST="bc.localhost:8000")
        detail_response = self.client.get(
            f"/api/v1/tryouts/{tryout.id}/",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_non_admin_cannot_create_tryout(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        user = User.objects.create_user(username="viewer", password="testpass")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/api/v1/tryouts/",
            {
                "region": bc.id,
                "association": assoc_bc.id,
                "name": "Nope",
                "start_date": "2025-01-10",
                "end_date": "2025-01-11",
                "location": "Field",
                "registration_url": "https://example.com",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 403)

    def test_coach_cannot_create_tryout(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        coach = User.objects.create_user(username="coach1", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.save()
        self.client.force_authenticate(user=coach)

        response = self.client.post(
            "/api/v1/tryouts/",
            {
                "region": bc.id,
                "association": assoc_bc.id,
                "name": "Nope",
                "start_date": "2025-01-10",
                "end_date": "2025-01-11",
                "location": "Field",
                "registration_url": "https://example.com",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 403)

    def test_approved_coach_can_create_tryout_for_assigned_team(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_bc = Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        coach = User.objects.create_user(username="coach2", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.save()
        TeamCoach.objects.create(user=coach, team=team_bc, is_active=True)
        self.client.force_authenticate(user=coach)

        response = self.client.post(
            "/api/v1/tryouts/",
            {
                "team": team_bc.id,
                "name": "Coach Tryout",
                "start_date": "2025-02-10",
                "end_date": "2025-02-11",
                "location": "Field",
                "registration_url": "https://example.com",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 201)
        tryout = TryoutEvent.objects.get(id=response.data["id"])
        self.assertEqual(tryout.association_id, assoc_bc.id)
        self.assertEqual(tryout.region_id, bc.id)
        self.assertTrue(AuditLog.objects.filter(action="TRYOUT_CREATED", target_id=tryout.id).exists())

    def test_coach_cannot_create_tryout_for_unassigned_team(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_bc = Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        coach = User.objects.create_user(username="coach3", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.save()
        self.client.force_authenticate(user=coach)

        response = self.client.post(
            "/api/v1/tryouts/",
            {
                "team": team_bc.id,
                "name": "Blocked Tryout",
                "start_date": "2025-03-10",
                "end_date": "2025-03-11",
                "location": "Field",
                "registration_url": "https://example.com",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 403)

    def test_tryout_api_filters_by_age_group(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_13 = Team.objects.create(region=bc, association=assoc_bc, name="Team 13U", age_group="13U")
        team_15 = Team.objects.create(region=bc, association=assoc_bc, name="Team 15U", age_group="15U", level="AAA")
        self._create_tryout(region=bc, association=assoc_bc, team=team_13, name="13U Tryout")
        self._create_tryout(region=bc, association=assoc_bc, team=team_15, name="15U Tryout")

        response = self.client.get(
            "/api/v1/tryouts/?age_group=13U",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["13U Tryout"])

        response = self.client.get(
            "/api/v1/tryouts/?level=AAA",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["15U Tryout"])

    def test_tryout_cancel_sets_inactive(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_bc = Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        coach = User.objects.create_user(username="coach4", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.save()
        TeamCoach.objects.create(user=coach, team=team_bc, is_active=True)
        tryout = self._create_tryout(region=bc, association=assoc_bc, team=team_bc, name="Cancel Me")

        self.client.force_authenticate(user=coach)
        response = self.client.delete(
            f"/api/v1/tryouts/{tryout.id}/",
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 204)
        tryout.refresh_from_db()
        self.assertFalse(tryout.is_active)
        self.assertTrue(AuditLog.objects.filter(action="TRYOUT_CANCELED", target_id=tryout.id).exists())


class TryoutModelTests(TestCase):
    def test_region_mismatch_validation(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_on = Team.objects.create(region=on, association=Association.objects.create(region=on, name="ON Assoc"), name="ON Team", age_group="13U")

        tryout = TryoutEvent(
            region=on,
            association=assoc_bc,
            team=team_on,
            name="Bad",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 11),
            location="Field",
            registration_url="https://example.com",
        )
        with self.assertRaises(ValidationError):
            tryout.full_clean()


class TryoutWebTests(TestCase):
    def _create_tryout(self, region, association, team=None, **kwargs):
        return TryoutEvent.objects.create(
            region=region,
            association=association,
            team=team,
            name=kwargs.get("name", "Tryout"),
            start_date=kwargs.get("start_date", date(2025, 1, 10)),
            end_date=kwargs.get("end_date", date(2025, 1, 11)),
            location=kwargs.get("location", "Field"),
            registration_url=kwargs.get("registration_url", "https://example.com"),
            is_active=kwargs.get("is_active", True),
        )

    def test_home_page_returns_200(self):
        response = self.client.get("/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)

    def test_tryouts_page_returns_200(self):
        response = self.client.get("/tryouts/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_for_anonymous(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_tryout_detail_is_region_scoped(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        assoc_on = Association.objects.create(region=on, name="ON Assoc")
        tryout = self._create_tryout(region=bc, association=assoc_bc, name="BC Tryout")
        self._create_tryout(region=on, association=assoc_on, name="ON Tryout")

        response = self.client.get(f"/tryouts/{tryout.id}/", HTTP_HOST="on.localhost:8000")
        self.assertEqual(response.status_code, 404)

    def test_coach_can_create_tryout_via_web(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team_bc = Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        coach = User.objects.create_user(username="coach_web", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = True
        coach.profile.save()
        TeamCoach.objects.create(user=coach, team=team_bc, is_active=True)

        self.assertTrue(self.client.login(username="coach_web", password="testpass"))
        response = self.client.post(
            "/coach/tryouts/new/",
            {
                "team": team_bc.id,
                "name": "Web Tryout",
                "start_date": "2025-04-10",
                "end_date": "2025-04-11",
                "location": "Field",
                "registration_url": "https://example.com",
            },
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 302)
        tryout = TryoutEvent.objects.get(name="Web Tryout")
        self.assertTrue(AuditLog.objects.filter(action="TRYOUT_CREATED", target_id=tryout.id).exists())

    def test_unapproved_coach_blocked_from_tryout_pages(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        coach = User.objects.create_user(username="coach_blocked", password="testpass")
        coach.profile.role = AccountProfile.Roles.COACH
        coach.profile.is_coach_approved = False
        coach.profile.save()

        self.assertTrue(self.client.login(username="coach_blocked", password="testpass"))
        response = self.client.get("/coach/tryouts/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 403)
