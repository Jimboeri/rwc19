from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from arena.models import Competition, Membership, PlayerRound, Prediction

from .factories import make_competition, make_game, make_membership, make_round, make_team, make_user


class SignupActivationJoinPickFlowTests(TestCase):
    """Walks the golden path end to end: signup -> activate -> login ->
    join a public competition -> submit a pick -> admin finishes the game ->
    points show up on the leaderboard."""

    def setUp(self):
        self.competition = make_competition()
        self.team1 = make_team(self.competition, "Home")
        self.team2 = make_team(self.competition, "Away")
        self.round = make_round(self.competition)
        self.game = make_game(
            self.round, self.team1, self.team2, gamedate=timezone.now() + timedelta(days=1)
        )

        self.admin_user = make_user(username="admin1")
        make_membership(self.competition, self.admin_user, role=Membership.Role.ADMIN)

    def test_full_golden_path(self):
        # Signup
        response = self.client.post(
            reverse("arena:signup"),
            {
                "email": "newplayer@example.com",
                "first_name": "New",
                "last_name": "Player",
                "password1": "a-strong-password1",
                "password2": "a-strong-password1",
            },
        )
        self.assertRedirects(response, reverse("arena:signup_done"))
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(username="newplayer@example.com")
        self.assertFalse(user.is_active)

        # Activate
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.get(reverse("arena:activate", args=[uid, token]))
        self.assertRedirects(response, reverse("arena:login"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Login
        response = self.client.post(
            reverse("arena:login"), {"username": "newplayer@example.com", "password": "a-strong-password1"}
        )
        self.assertRedirects(response, reverse("arena:dashboard"))

        # Join the public competition
        response = self.client.post(reverse("arena:join", args=[self.competition.slug]))
        self.assertRedirects(response, reverse("arena:competition_home", args=[self.competition.slug]))
        self.assertTrue(Membership.objects.filter(user=user, competition=self.competition).exists())

        # Submit a pick
        membership = Membership.objects.get(user=user, competition=self.competition)
        player_round = PlayerRound.objects.get(membership=membership, round=self.round)
        prediction = Prediction.objects.get(player_round=player_round, game=self.game)

        response = self.client.post(
            reverse("arena:pick_update", args=[self.competition.slug, self.round.id]),
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": prediction.id,
                "form-0-result": Prediction.Result.TEAM1,
                "form-0-spread": 10,
            },
        )
        self.assertRedirects(
            response, reverse("arena:disp_round", args=[self.competition.slug, user.id, self.round.id])
        )
        prediction.refresh_from_db()
        self.assertEqual(prediction.result, Prediction.Result.TEAM1)
        self.assertEqual(prediction.spread, 10)

        # Admin finishes the game
        self.client.logout()
        self.client.force_login(self.admin_user)

        admin_predictions_qs = self.game.predictions.order_by("points", "player_round__membership__user__username")
        post_data = {
            "gamedate": self.game.gamedate.strftime("%Y-%m-%d %H:%M:%S"),
            "score1": "20",
            "score2": "10",
            "finished": "on",
            "form-TOTAL_FORMS": str(admin_predictions_qs.count()),
            "form-INITIAL_FORMS": str(admin_predictions_qs.count()),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        for i, pred in enumerate(admin_predictions_qs):
            post_data[f"form-{i}-id"] = pred.id
            post_data[f"form-{i}-result"] = pred.result
            post_data[f"form-{i}-spread"] = pred.spread
            if pred.override:
                post_data[f"form-{i}-override"] = "on"

        response = self.client.post(
            reverse("arena:game_edit", args=[self.competition.slug, self.game.id]), post_data
        )
        self.assertRedirects(response, reverse("arena:game_view", args=[self.competition.slug, self.game.id]))

        prediction.refresh_from_db()
        self.assertEqual(prediction.points, 20)  # correct winner, exact margin

        player_round.refresh_from_db()
        self.assertEqual(player_round.total_points, 20)


class DashboardTests(TestCase):
    def test_dashboard_lists_memberships_and_joinable_competitions(self):
        joined = make_competition(name="Joined Cup", slug="joined-cup")
        joinable = make_competition(name="Joinable Cup", slug="joinable-cup")
        make_competition(
            name="Invite Only Cup", slug="invite-only-cup", visibility=Competition.Visibility.INVITE
        )

        user = make_user()
        make_membership(joined, user)
        self.client.force_login(user)

        response = self.client.get(reverse("arena:dashboard"))

        self.assertContains(response, "Joined Cup")
        self.assertContains(response, "Joinable Cup")
        self.assertNotContains(response, "Invite Only Cup")


class SuperadminCompetitionTests(TestCase):
    def test_non_superuser_cannot_create_competition(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.get(reverse("arena:superadmin_competition_create"))
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_create_competition_and_assign_admin(self):
        superuser = make_user(username="root", is_superuser=True, is_staff=True)
        prospective_admin = make_user(username="future-admin")
        self.client.force_login(superuser)

        response = self.client.post(
            reverse("arena:superadmin_competition_create"),
            {
                "name": "Brand New Cup",
                "slug": "brand-new-cup",
                "description": "",
                "kind": Competition.Kind.SERIES,
                "status": Competition.Status.OPEN,
                "visibility": Competition.Visibility.PUBLIC,
                "default_entry_fee": "5.00",
                "scoring_rules": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        competition = Competition.objects.get(slug="brand-new-cup")

        response = self.client.post(
            reverse("arena:superadmin_competition_admins", args=[competition.slug]),
            {"email": prospective_admin.username},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Membership.objects.filter(
                user=prospective_admin, competition=competition, role=Membership.Role.ADMIN
            ).exists()
        )
