import json
from pathlib import Path

from django.contrib.auth.models import User

from arena.models import Competition, Game, Membership, PlayerRound, Round, Team

EXAMPLE_RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "example_margin_scoring.json"


def load_example_scoring_rules():
    return json.loads(EXAMPLE_RULES_PATH.read_text())


def make_competition(name="Test Cup", slug="test-cup", with_rules=True, **kwargs):
    defaults = {
        "visibility": Competition.Visibility.PUBLIC,
        "status": Competition.Status.ACTIVE,
    }
    defaults.update(kwargs)
    if with_rules and "scoring_rules" not in defaults:
        defaults["scoring_rules"] = load_example_scoring_rules()
    return Competition.objects.create(name=name, slug=slug, **defaults)


def make_user(username="player1", **kwargs):
    user = User.objects.create_user(username=username, email=username, password="password123")
    for key, value in kwargs.items():
        setattr(user, key, value)
    user.save()
    return user


def make_membership(competition, user, role=Membership.Role.PLAYER):
    membership, _ = Membership.objects.get_or_create(user=user, competition=competition, defaults={"role": role})
    return membership


def make_team(competition, name):
    return Team.objects.create(competition=competition, name=name, code=name[:3].upper())


def make_round(competition, name="Round 1", order=1, status=Round.Status.CURRENT):
    return Round.objects.create(competition=competition, name=name, order=order, status=status)


def make_game(round_obj, team1, team2, **kwargs):
    return Game.objects.create(round=round_obj, team1=team1, team2=team2, **kwargs)


def make_player_round(membership, round_obj):
    player_round, _ = PlayerRound.objects.get_or_create(membership=membership, round=round_obj)
    player_round.ensure_predictions()
    return player_round
