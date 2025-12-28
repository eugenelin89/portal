from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from organizations.models import Association, Team
from regions.models import Region


User = get_user_model()


class OrganizationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="viewer", password="testpass")
        self.client.force_authenticate(user=self.user)

    def test_associations_filtered_by_region(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        Association.objects.create(region=bc, name="BC Assoc")
        Association.objects.create(region=on, name="ON Assoc")

        response = self.client.get("/api/v1/associations/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["BC Assoc"])

    def test_teams_filtered_by_region(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        assoc_on = Association.objects.create(region=on, name="ON Assoc")
        Team.objects.create(region=bc, association=assoc_bc, name="BC Team", age_group="13U")
        Team.objects.create(region=on, association=assoc_on, name="ON Team", age_group="13U")

        response = self.client.get("/api/v1/teams/", HTTP_HOST="bc.localhost:8000")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["BC Team"])

    def test_non_admin_cannot_create_association(self):
        bc = Region.objects.get(code="bc")
        response = self.client.post(
            "/api/v1/associations/",
            {"region": bc.id, "name": "Nope"},
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 405)

    def test_non_admin_cannot_create_team(self):
        bc = Region.objects.get(code="bc")
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        response = self.client.post(
            "/api/v1/teams/",
            {"region": bc.id, "association": assoc_bc.id, "name": "Nope", "age_group": "13U"},
            HTTP_HOST="bc.localhost:8000",
        )
        self.assertEqual(response.status_code, 405)


class OrganizationModelTests(TestCase):
    def test_team_region_must_match_association_region(self):
        bc = Region.objects.get(code="bc")
        on = Region.objects.create(code="on", name="Ontario", is_active=True)
        assoc_bc = Association.objects.create(region=bc, name="BC Assoc")
        team = Team(region=on, association=assoc_bc, name="Bad Team", age_group="13U")
        with self.assertRaises(ValidationError):
            team.full_clean()
