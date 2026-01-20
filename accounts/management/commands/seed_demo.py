from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AccountProfile
from availability.models import PlayerAvailability
from organizations.models import Association, Team, TeamCoach
from profiles.models import PlayerProfile
from regions.models import Region
from tryouts.models import TryoutEvent


class Command(BaseCommand):
    help = "Seed minimal, deterministic demo data."

    def handle(self, *args, **options):
        user_model = get_user_model()

        bc, _ = Region.objects.get_or_create(
            code="bc",
            defaults={"name": "British Columbia", "is_active": True},
        )

        association, _ = Association.objects.get_or_create(
            region=bc,
            name="Vancouver Minor Baseball",
            defaults={"short_name": "VMB", "is_active": True},
        )

        team_13_aaa, _ = Team.objects.get_or_create(
            region=bc,
            association=association,
            name="VMB 13U AAA",
            defaults={"age_group": "13U", "level": "AAA", "is_active": True},
        )
        Team.objects.get_or_create(
            region=bc,
            association=association,
            name="VMB 13U AA",
            defaults={"age_group": "13U", "level": "AA", "is_active": True},
        )
        Team.objects.get_or_create(
            region=bc,
            association=association,
            name="VMB 15U AAA",
            defaults={"age_group": "15U", "level": "AAA", "is_active": True},
        )

        admin_user, _ = user_model.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )
        admin_user.email = "admin@example.com"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("adminpass123")
        admin_user.save()

        coach_user, _ = user_model.objects.get_or_create(
            username="coach1",
            defaults={"email": "coach1@example.com"},
        )
        coach_user.email = "coach1@example.com"
        coach_user.set_password("coachpass123")
        coach_user.save()
        coach_user.profile.role = AccountProfile.Roles.COACH
        coach_user.profile.is_coach_approved = True
        coach_user.profile.save()

        player_user, _ = user_model.objects.get_or_create(
            username="player1",
            defaults={"email": "player1@example.com"},
        )
        player_user.email = "player1@example.com"
        player_user.set_password("playerpass123")
        player_user.save()
        player_user.profile.role = AccountProfile.Roles.PLAYER
        player_user.profile.save()

        TeamCoach.objects.get_or_create(
            user=coach_user,
            team=team_13_aaa,
            defaults={"is_active": True},
        )

        profile, _ = PlayerProfile.objects.get_or_create(user=player_user)
        profile.display_name = "J. Player"
        profile.birth_year = 2011
        profile.positions = ["OF"]
        profile.bats = PlayerProfile.Bats.RIGHT
        profile.throws = PlayerProfile.Throws.RIGHT
        profile.current_association = association
        profile.profile_visibility = PlayerProfile.Visibility.SPECIFIC
        profile.save()
        profile.visible_associations.set([association])

        availability, _ = PlayerAvailability.objects.get_or_create(
            player=player_user,
            defaults={"region": bc},
        )
        availability.region = bc
        availability.is_open = True
        availability.is_committed = False
        availability.committed_at = None
        availability.expires_at = None
        availability.positions = ["OF"]
        availability.levels = ["AAA"]
        availability.save()
        availability.allowed_associations.set([team_13_aaa.association])

        start_date = timezone.localdate() + timedelta(days=7)
        end_date = start_date + timedelta(days=1)
        tryout, _ = TryoutEvent.objects.get_or_create(
            region=bc,
            association=association,
            team=team_13_aaa,
            name="13U AAA Tryouts",
            defaults={
                "start_date": start_date,
                "end_date": end_date,
                "location": "Vancouver",
                "registration_url": "https://example.com/tryouts",
                "is_active": True,
            },
        )
        tryout.start_date = start_date
        tryout.end_date = end_date
        tryout.location = "Vancouver"
        tryout.registration_url = "https://example.com/tryouts"
        tryout.is_active = True
        tryout.save()

        self.stdout.write("Seed complete. Demo credentials:")
        self.stdout.write("- admin / adminpass123 (superuser)")
        self.stdout.write("- coach1 / coachpass123 (approved coach)")
        self.stdout.write("- player1 / playerpass123 (player)")
        self.stdout.write("\nDemo objects:")
        self.stdout.write(f"- Region: {bc.code} ({bc.name})")
        self.stdout.write(f"- Association: {association.name}")
        self.stdout.write(f"- Team: {team_13_aaa.name}")
        self.stdout.write(f"- Tryout: {tryout.name} on {tryout.start_date}")
        self.stdout.write("\nContact request demo (run manually):")
        self.stdout.write(
            "curl -X POST http://bc.localhost:8000/api/v1/contact-requests/ "
            "-H 'Authorization: Bearer <coach_access_token>' "
            "-H 'Content-Type: application/json' "
            "-d '{\"player_id\":%d,\"requesting_team_id\":%d,\"message\":\"We would like to connect.\"}'"
            % (player_user.id, team_13_aaa.id)
        )
