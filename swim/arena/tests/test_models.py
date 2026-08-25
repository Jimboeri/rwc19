from django.db import IntegrityError, transaction
from django.test import TestCase

from arena.models import Membership, Prediction, Round
from arena.rules import ScoringRulesError, evaluate_score

from .factories import make_competition, make_game, make_membership, make_player_round, make_round, make_team, make_user


class ScoringRulesEngineTests(TestCase):
    """
    Exercises the real zen-engine against swim/arena/rules/example_margin_scoring.json,
    which reproduces the classic RWC win-margin/draw scoring as a JDM decision table.
    """

    def setUp(self):
        self.competition = make_competition()

    def score(self, predicted_result, actual_result, predicted_spread=0, actual_spread=0):
        return evaluate_score(
            self.competition,
            {
                "predictedResult": predicted_result,
                "actualResult": actual_result,
                "predictedSpread": predicted_spread,
                "actualSpread": actual_spread,
            },
        )

    def test_correct_draw_scores_25(self):
        self.assertEqual(self.score(3, 3), 25)

    def test_correct_win_with_exact_margin_scores_20(self):
        self.assertEqual(self.score(1, 1, predicted_spread=10, actual_spread=10), 20)

    def test_correct_win_margin_scoring_table(self):
        expected_by_diff = {0: 20, 1: 19, 5: 15, 10: 10, 14: 6}
        for diff, expected_points in expected_by_diff.items():
            with self.subTest(diff=diff):
                self.assertEqual(self.score(1, 1, predicted_spread=0, actual_spread=diff), expected_points)

    def test_correct_win_beyond_15_margin_floors_at_5(self):
        self.assertEqual(self.score(1, 1, predicted_spread=0, actual_spread=15), 5)
        self.assertEqual(self.score(2, 2, predicted_spread=0, actual_spread=40), 5)

    def test_wrong_result_scores_0(self):
        self.assertEqual(self.score(1, 2, predicted_spread=5, actual_spread=5), 0)

    def test_no_selection_scores_0(self):
        self.assertEqual(self.score(0, 1, predicted_spread=0, actual_spread=5), 0)

    def test_missing_rules_raise(self):
        competition = make_competition(name="No Rules", slug="no-rules", with_rules=False)
        with self.assertRaises(ScoringRulesError):
            evaluate_score(competition, {"predictedResult": 1, "actualResult": 1, "predictedSpread": 0, "actualSpread": 0})


class PredictionCalcScoreTests(TestCase):
    def setUp(self):
        self.competition = make_competition()
        self.team1 = make_team(self.competition, "Home")
        self.team2 = make_team(self.competition, "Away")
        self.round = make_round(self.competition)
        self.user = make_user()
        self.membership = make_membership(self.competition, self.user)
        self.player_round = make_player_round(self.membership, self.round)

    def test_calc_score_ignores_unfinished_games(self):
        game = make_game(self.round, self.team1, self.team2, finished=False)
        prediction = Prediction.objects.get(player_round=self.player_round, game=game)
        prediction.result = Prediction.Result.TEAM1
        prediction.spread = 10
        prediction.save()

        self.assertEqual(prediction.calc_score(), 0)

    def test_calc_score_awards_points_once_finished(self):
        game = make_game(self.round, self.team1, self.team2, finished=True, score1=20, score2=10)
        prediction = Prediction.objects.get(player_round=self.player_round, game=game)
        prediction.result = Prediction.Result.TEAM1
        prediction.spread = 10
        prediction.save()

        self.assertEqual(prediction.calc_score(), 20)

    def test_calc_score_falls_back_to_zero_when_rules_missing(self):
        competition = make_competition(name="No Rules 2", slug="no-rules-2", with_rules=False)
        team1 = make_team(competition, "Home")
        team2 = make_team(competition, "Away")
        round_obj = make_round(competition)
        membership = make_membership(competition, self.user)
        player_round = make_player_round(membership, round_obj)
        game = make_game(round_obj, team1, team2, finished=True, score1=10, score2=0)
        prediction = Prediction.objects.get(player_round=player_round, game=game)
        prediction.result = Prediction.Result.TEAM1
        prediction.save()

        self.assertEqual(prediction.calc_score(), 0)


class PlayerRoundTests(TestCase):
    def setUp(self):
        self.competition = make_competition()
        self.team1 = make_team(self.competition, "Home")
        self.team2 = make_team(self.competition, "Away")
        self.round = make_round(self.competition)
        self.user = make_user()
        self.membership = make_membership(self.competition, self.user)

    def test_recalc_total_sums_only_finished_games(self):
        player_round = make_player_round(self.membership, self.round)
        finished_game = make_game(self.round, self.team1, self.team2, finished=True, score1=20, score2=10)
        unfinished_game = make_game(self.round, self.team1, self.team2, finished=False)

        finished_pred = Prediction.objects.get(player_round=player_round, game=finished_game)
        finished_pred.result = Prediction.Result.TEAM1
        finished_pred.spread = 10
        finished_pred.save()

        unfinished_pred = Prediction.objects.get(player_round=player_round, game=unfinished_game)
        unfinished_pred.result = Prediction.Result.TEAM1
        unfinished_pred.spread = 10
        unfinished_pred.save()

        player_round.recalc_total()

        self.assertEqual(player_round.total_points, 20)


class MembershipTests(TestCase):
    def test_ensure_player_rounds_creates_rounds_and_predictions(self):
        competition = make_competition()
        team1 = make_team(competition, "Home")
        team2 = make_team(competition, "Away")
        round1 = make_round(competition, name="Round 1", order=1)
        make_game(round1, team1, team2)
        user = make_user()
        membership = make_membership(competition, user)

        membership.ensure_player_rounds()

        self.assertEqual(membership.player_rounds.count(), 1)
        self.assertEqual(membership.player_rounds.first().predictions.count(), 1)

    def test_unique_membership_per_competition(self):
        competition = make_competition()
        user = make_user()
        make_membership(competition, user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(user=user, competition=competition)


class RoundStatusTests(TestCase):
    def test_refresh_round_statuses_marks_current_and_finished(self):
        competition = make_competition()
        team1 = make_team(competition, "Home")
        team2 = make_team(competition, "Away")
        round1 = make_round(competition, name="Round 1", order=1, status=Round.Status.NOT_STARTED)
        round2 = make_round(competition, name="Round 2", order=2, status=Round.Status.NOT_STARTED)
        make_game(round1, team1, team2, finished=True, score1=10, score2=0)
        make_game(round2, team1, team2, finished=False)

        competition.refresh_round_statuses()

        round1.refresh_from_db()
        round2.refresh_from_db()
        self.assertEqual(round1.status, Round.Status.FINISHED)
        self.assertEqual(round2.status, Round.Status.CURRENT)

    def test_round_with_no_games_is_not_auto_finished(self):
        competition = make_competition()
        empty_round = make_round(competition, status=Round.Status.NOT_STARTED)

        competition.refresh_round_statuses()

        empty_round.refresh_from_db()
        self.assertEqual(empty_round.status, Round.Status.CURRENT)
