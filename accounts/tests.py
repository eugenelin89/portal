from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from accounts.models import AccountProfile
from accounts.permissions import IsAdminRole, IsApprovedCoach


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
