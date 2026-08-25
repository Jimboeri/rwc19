from django.test import TestCase
from django.urls import reverse

from arena.models import Competition, Membership

from .factories import make_competition, make_game, make_membership, make_round, make_team, make_user


class CompetitionMemberRequiredTests(TestCase):
    def setUp(self):
        self.public_competition = make_competition(name="Public Cup", slug="public-cup")
        self.invite_competition = make_competition(
            name="Invite Cup", slug="invite-cup", visibility=Competition.Visibility.INVITE
        )
        self.user = make_user()

    def test_anonymous_user_redirected_to_arena_login(self):
        response = self.client.get(reverse("arena:competition_home", args=[self.public_competition.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("arena:login"), response.url)

    def test_non_member_redirected_to_join_for_public_competition(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("arena:competition_home", args=[self.public_competition.slug]))
        self.assertRedirects(response, reverse("arena:join", args=[self.public_competition.slug]))

    def test_non_member_forbidden_for_invite_only_competition(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("arena:competition_home", args=[self.invite_competition.slug]))
        self.assertEqual(response.status_code, 403)

    def test_member_can_view_competition_home(self):
        make_membership(self.public_competition, self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("arena:competition_home", args=[self.public_competition.slug]))
        self.assertEqual(response.status_code, 200)


class CompetitionAdminRequiredTests(TestCase):
    def setUp(self):
        self.competition = make_competition()
        self.player = make_user(username="player1")
        self.admin_user = make_user(username="admin1")
        make_membership(self.competition, self.player, role=Membership.Role.PLAYER)
        make_membership(self.competition, self.admin_user, role=Membership.Role.ADMIN)

    def test_player_forbidden_from_admin_view(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("arena:admin_teams", args=[self.competition.slug]))
        self.assertEqual(response.status_code, 403)

    def test_competition_admin_can_access_admin_view(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("arena:admin_teams", args=[self.competition.slug]))
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access_admin_view_without_membership(self):
        superuser = make_user(username="root", is_superuser=True, is_staff=True)
        self.client.force_login(superuser)
        response = self.client.get(reverse("arena:admin_teams", args=[self.competition.slug]))
        self.assertEqual(response.status_code, 200)


class CrossCompetitionIsolationTests(TestCase):
    """An admin of competition A must not be able to reach competition B's data
    through competition A's admin URLs, even if they guess an id."""

    def setUp(self):
        self.competition_a = make_competition(name="Comp A", slug="comp-a")
        self.competition_b = make_competition(name="Comp B", slug="comp-b")
        self.admin_a = make_user(username="admin-a")
        make_membership(self.competition_a, self.admin_a, role=Membership.Role.ADMIN)

        team1 = make_team(self.competition_b, "Home")
        team2 = make_team(self.competition_b, "Away")
        round_b = make_round(self.competition_b)
        self.game_in_b = make_game(round_b, team1, team2)

    def test_admin_of_a_cannot_edit_game_from_b_via_as_slug(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(
            reverse("arena:game_edit", args=[self.competition_a.slug, self.game_in_b.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_of_a_is_forbidden_from_b_admin_urls_outright(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("arena:admin_teams", args=[self.competition_b.slug]))
        self.assertEqual(response.status_code, 403)
