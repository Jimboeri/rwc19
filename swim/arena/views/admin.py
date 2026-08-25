from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import AdminMembershipForm, AdminPickForm, AdminUserForm, GameCreateForm, GameForm, RoundForm, TeamForm
from ..models import Game, Membership, PlayerRound, Prediction, Round, Team
from ..permissions import competition_admin_required


@competition_admin_required
def team_list(request, slug):
    competition = request.competition
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.competition = competition
            team.save()
            return redirect("arena:admin_teams", slug=slug)
    else:
        form = TeamForm()

    context = {"competition": competition, "teams": competition.teams.all(), "form": form}
    return render(request, "arena/admin/team_list.html", context)


@competition_admin_required
@require_POST
def team_delete(request, slug, team_id):
    team = get_object_or_404(Team, id=team_id, competition=request.competition)
    team.delete()
    return redirect("arena:admin_teams", slug=slug)


@competition_admin_required
def round_list(request, slug):
    competition = request.competition
    if request.method == "POST":
        form = RoundForm(request.POST)
        if form.is_valid():
            round_obj = form.save(commit=False)
            round_obj.competition = competition
            round_obj.save()
            return redirect("arena:admin_rounds", slug=slug)
    else:
        form = RoundForm()

    context = {"competition": competition, "rounds": competition.rounds.all(), "form": form}
    return render(request, "arena/admin/round_list.html", context)


@competition_admin_required
@require_POST
def refresh_rounds(request, slug):
    request.competition.refresh_round_statuses()
    return redirect("arena:admin_rounds", slug=slug)


@competition_admin_required
def round_games(request, slug, round_id):
    competition = request.competition
    round_obj = get_object_or_404(Round, id=round_id, competition=competition)

    if request.method == "POST":
        form = GameCreateForm(request.POST, competition=competition)
        if form.is_valid():
            game = form.save(commit=False)
            game.round = round_obj
            game.save()
            return redirect("arena:admin_round_games", slug=slug, round_id=round_id)
    else:
        form = GameCreateForm(competition=competition)

    context = {"competition": competition, "round": round_obj, "games": round_obj.games.all(), "form": form}
    return render(request, "arena/admin/round_games.html", context)


@competition_admin_required
def game_edit(request, slug, game_id):
    competition = request.competition
    game = get_object_or_404(Game, id=game_id, round__competition=competition)

    # Make sure every current member has a prediction row for this game before editing.
    for membership in competition.memberships.filter(role=Membership.Role.PLAYER, blocked=False):
        player_round, _ = PlayerRound.objects.get_or_create(membership=membership, round=game.round)
        Prediction.objects.get_or_create(player_round=player_round, game=game)

    PickFormSet = modelformset_factory(Prediction, form=AdminPickForm, extra=0)
    predictions_qs = game.predictions.order_by("points", "player_round__membership__user__username")

    if request.method == "POST":
        game_form = GameForm(request.POST, instance=game)
        formset = PickFormSet(request.POST, queryset=predictions_qs)

        if game_form.is_valid() and formset.is_valid():
            game_form.save()
            formset.save()
            for pick in predictions_qs:
                if pick.result == Prediction.Result.DRAW and pick.spread != 0:
                    pick.spread = 0
                    pick.save(update_fields=["spread"])

            if game.finished:
                game.compute_result_text()
                for pick in predictions_qs:
                    if not pick.override:
                        pick.calc_score()
                        pick.player_round.recalc_total()

            return redirect("arena:game_view", slug=slug, game_id=game.id)
    else:
        game_form = GameForm(instance=game)
        formset = PickFormSet(queryset=predictions_qs)

    context = {"competition": competition, "game": game, "game_form": game_form, "formset": formset}
    return render(request, "arena/admin/game_edit.html", context)


@competition_admin_required
def player_list(request, slug):
    competition = request.competition
    memberships = competition.memberships.select_related("user").order_by("user__first_name")
    for membership in memberships:
        membership.ensure_player_rounds()
    return render(request, "arena/admin/player_list.html", {"competition": competition, "memberships": memberships})


@competition_admin_required
def player_detail(request, slug, user_id):
    competition = request.competition
    player = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(Membership, user=player, competition=competition)

    if request.method == "POST":
        user_form = AdminUserForm(request.POST, instance=player)
        membership_form = AdminMembershipForm(request.POST, instance=membership)
        if user_form.is_valid() and membership_form.is_valid():
            user_form.save()
            membership_form.save()
            return redirect("arena:admin_players", slug=slug)
    else:
        user_form = AdminUserForm(instance=player)
        membership_form = AdminMembershipForm(instance=membership)

    context = {"competition": competition, "player": player, "user_form": user_form, "membership_form": membership_form}
    return render(request, "arena/admin/player_detail.html", context)


@competition_admin_required
def player_payment(request, slug, user_id):
    competition = request.competition
    player = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(Membership, user=player, competition=competition)

    RoundFormSet = modelformset_factory(PlayerRound, fields=["paid", "paid_amount"], extra=0)
    queryset = membership.player_rounds.select_related("round")

    if request.method == "POST":
        formset = RoundFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            for player_round in queryset:
                player_round.paid = player_round.is_paid_in_full
                player_round.save(update_fields=["paid"])
            membership.recalc_fully_paid()
            return redirect("arena:admin_players", slug=slug)
    else:
        formset = RoundFormSet(queryset=queryset)

    context = {"competition": competition, "player": player, "formset": formset}
    return render(request, "arena/admin/player_payment.html", context)


@competition_admin_required
@require_POST
def player_full_payment(request, slug, user_id):
    competition = request.competition
    player = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(Membership, user=player, competition=competition)

    for player_round in membership.player_rounds.select_related("round"):
        player_round.paid = True
        player_round.paid_amount = player_round.round.effective_entry_fee
        player_round.save(update_fields=["paid", "paid_amount"])
    membership.recalc_fully_paid()

    return redirect("arena:admin_players", slug=slug)
