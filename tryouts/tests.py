from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from organizations.models import Association, Team
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
