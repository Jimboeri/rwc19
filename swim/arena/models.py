import logging
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .rules import ScoringRulesError, evaluate_score

logger = logging.getLogger(__name__)


class CompetitionQuerySet(models.QuerySet):
    def public(self):
        return self.filter(visibility=Competition.Visibility.PUBLIC)

    def joinable(self):
        return self.public().filter(
            status__in=[Competition.Status.OPEN, Competition.Status.ACTIVE]
        )


class Competition(models.Model):
    class Kind(models.TextChoices):
        TOURNAMENT = "TOURNAMENT", "Tournament"
        SERIES = "SERIES", "Series"
        LEAGUE = "LEAGUE", "League"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open for registration"
        ACTIVE = "ACTIVE", "Active"
        FINISHED = "FINISHED", "Finished"
        ARCHIVED = "ARCHIVED", "Archived"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public - anyone can join"
        INVITE = "INVITE", "Invite only"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True, default="")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.TOURNAMENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.INVITE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    default_entry_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("5.00"))
    scoring_rules = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "GoRules ZEN Engine JDM decision graph used to score predictions once a "
            "game is finished. See swim/arena/rules/example_margin_scoring.json for "
            "a worked example reproducing the classic win-margin/draw scoring, and "
            "arena/rules.py for the facts passed in (predictedResult, actualResult, "
            "predictedSpread, actualSpread) and the required 'points' output. "
            "Predictions cannot be scored until this is set."
        ),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competitions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CompetitionQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("arena:competition_home", args=[self.slug])

    def is_admin(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self.memberships.filter(
            user=user, role=Membership.Role.ADMIN, blocked=False
        ).exists()

    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return user.is_superuser or self.memberships.filter(user=user).exists()

    def refresh_round_statuses(self):
        """
        Mark rounds finished once every game in them is finished, and flag the
        first not-yet-finished round as current. Only ever triggered explicitly
        by a competition admin, never as a side effect of a player viewing a page.
        """
        current_assigned = False
        for rnd in self.rounds.all():
            if rnd.games.exists() and not rnd.games.filter(finished=False).exists():
                rnd.status = Round.Status.FINISHED
            elif not current_assigned:
                rnd.status = Round.Status.CURRENT
                current_assigned = True
            else:
                rnd.status = Round.Status.NOT_STARTED
            rnd.save(update_fields=["status"])


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        PLAYER = "PLAYER", "Player"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PLAYER)
    phone_number = models.CharField(max_length=50, blank=True, default="")
    blocked = models.BooleanField(default=False)
    fully_paid = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["competition__name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "competition"], name="unique_membership_per_competition")
        ]

    def __str__(self):
        return f"{self.user} in {self.competition} ({self.role})"

    @property
    def is_admin(self):
        return self.role == Membership.Role.ADMIN or self.user.is_superuser

    def ensure_player_rounds(self):
        """Ensure a PlayerRound (and its predictions) exists for every round in this competition."""
        for rnd in self.competition.rounds.all():
            player_round, _ = PlayerRound.objects.get_or_create(membership=self, round=rnd)
            player_round.ensure_predictions()

    def recalc_fully_paid(self):
        fully_paid = all(
            pr.is_paid_in_full for pr in self.player_rounds.select_related("round")
        )
        if fully_paid != self.fully_paid:
            self.fully_paid = fully_paid
            self.save(update_fields=["fully_paid"])
        return self.fully_paid


class Team(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=100)
    descr = models.TextField(blank=True, default="")
    pool = models.CharField(max_length=1, blank=True, default="")
    code = models.CharField(max_length=3, blank=True, default="")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["competition", "name"], name="unique_team_name_per_competition")
        ]

    def __str__(self):
        return self.name


class Round(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "N", "Not current"
        CURRENT = "C", "Current"
        FINISHED = "F", "Finished"

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="rounds")
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0, help_text="Order of round")
    start = models.DateTimeField(blank=True, null=True)
    finish = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.NOT_STARTED)
    entry_fee = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Overrides the competition's default entry fee if set",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.competition} - {self.name}"

    @property
    def effective_entry_fee(self):
        return self.entry_fee if self.entry_fee is not None else self.competition.default_entry_fee


class Game(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="games")
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="games_as_team1")
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="games_as_team2")
    gamedate = models.DateTimeField(blank=True, null=True)
    score1 = models.PositiveIntegerField(default=0, help_text="Score of 1st team")
    score2 = models.PositiveIntegerField(default=0, help_text="Score of 2nd team")
    finished = models.BooleanField(default=False)
    high_point = models.FloatField(default=0)
    average = models.DecimalField(default=0, max_digits=5, decimal_places=1)
    result_text = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["round__order", "gamedate"]

    def __str__(self):
        return f"{self.team1} v {self.team2}"

    def short_name(self):
        return f"{self.team1.code} v {self.team2.code}"

    def result(self):
        """0 = not finished, 1 = team1 win, 2 = team2 win, 3 = draw."""
        if not self.finished:
            return 0
        if self.score1 > self.score2:
            return 1
        if self.score1 < self.score2:
            return 2
        return 3

    def spread(self):
        return abs(self.score1 - self.score2) if self.finished else 0

    @property
    def has_started(self):
        return bool(self.gamedate) and self.gamedate < timezone.now()

    def compute_result_text(self):
        if not self.finished:
            text = "Game not finished"
        elif self.score1 > self.score2:
            text = f"{self.team1.name} win by {self.score1 - self.score2}"
        elif self.score1 < self.score2:
            text = f"{self.team2.name} win by {self.score2 - self.score1}"
        else:
            text = "Draw"
        self.result_text = text
        self.save(update_fields=["result_text"])
        return text


class PlayerRound(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="player_rounds")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="player_rounds")
    total_points = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(default=0, max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["round__order"]
        constraints = [
            models.UniqueConstraint(fields=["membership", "round"], name="unique_player_round")
        ]

    def __str__(self):
        return f"{self.membership.user} : {self.round}"

    @property
    def is_paid_in_full(self):
        return self.paid_amount >= self.round.effective_entry_fee

    def ensure_predictions(self):
        for game in self.round.games.all():
            Prediction.objects.get_or_create(player_round=self, game=game)

    def recalc_total(self):
        self.ensure_predictions()
        total = 0
        for prediction in self.predictions.select_related("game"):
            prediction.calc_score()
            if prediction.game.finished:
                total += prediction.points
        if total != self.total_points:
            self.total_points = total
            self.save(update_fields=["total_points", "last_updated"])


class Prediction(models.Model):
    class Result(models.IntegerChoices):
        NONE = 0, "No selection"
        TEAM1 = 1, "Team 1 wins"
        TEAM2 = 2, "Team 2 wins"
        DRAW = 3, "Draw"

    player_round = models.ForeignKey(PlayerRound, on_delete=models.CASCADE, related_name="predictions")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="predictions")
    result = models.IntegerField(choices=Result.choices, default=Result.NONE)
    spread = models.PositiveIntegerField(default=0, help_text="Predicted winning margin")
    points = models.FloatField(default=0)
    override = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["game__gamedate"]
        constraints = [
            models.UniqueConstraint(fields=["player_round", "game"], name="unique_prediction_per_game")
        ]

    def __str__(self):
        return f"{self.player_round.membership.user} : {self.game}"

    def calc_score(self):
        if not self.game.finished:
            return self.points

        competition = self.player_round.membership.competition
        facts = {
            "predictedResult": self.result,
            "actualResult": self.game.result(),
            "predictedSpread": self.spread,
            "actualSpread": self.game.spread(),
        }
        try:
            points = evaluate_score(competition, facts)
        except ScoringRulesError:
            logger.warning(
                "Could not score prediction %s for competition '%s'", self.pk, competition, exc_info=True
            )
            points = 0

        self.points = points
        self.save(update_fields=["points", "last_updated"])
        return self.points

    @property
    def result_text(self):
        if self.result == Prediction.Result.TEAM1:
            return f"{self.game.team1.name} by {self.spread}"
        if self.result == Prediction.Result.TEAM2:
            return f"{self.game.team2.name} by {self.spread}"
        if self.result == Prediction.Result.DRAW:
            return "Draw"
        return "No selection"

    def spread_diff(self):
        return abs(self.spread - self.game.spread()) if self.game.finished else 0
