from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from regions.models import Region
from transferportal.middleware.region import RegionMiddleware


class RegionMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.captured_request = None

        def get_response(request):
            self.captured_request = request
            return HttpResponse("ok")

        self.middleware = RegionMiddleware(get_response)

    def test_bc_subdomain_sets_region_code(self):
        request = self.factory.get("/", HTTP_HOST="bc.localhost:8000")
        self.middleware(request)
        self.assertEqual(self.captured_request.region_code, "bc")

    def test_localhost_defaults_to_bc(self):
        request = self.factory.get("/", HTTP_HOST="localhost:8000")
        self.middleware(request)
        self.assertEqual(self.captured_request.region_code, "bc")

    def test_on_subdomain_sets_region_code(self):
        Region.objects.create(code="on", name="Ontario", is_active=True)
        request = self.factory.get("/", HTTP_HOST="on.localhost:8000")
        self.middleware(request)
        self.assertEqual(self.captured_request.region_code, "on")
