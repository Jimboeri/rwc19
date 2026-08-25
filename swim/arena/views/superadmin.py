from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import CompetitionForm
from ..models import Competition, Membership
from ..permissions import get_competition_or_404, superadmin_required


@superadmin_required
def competition_list(request):
    competitions = Competition.objects.all()
    return render(request, "arena/admin/superadmin/competition_list.html", {"competitions": competitions})


@superadmin_required
def competition_create(request):
    if request.method == "POST":
        form = CompetitionForm(request.POST)
        if form.is_valid():
            competition = form.save(commit=False)
            competition.created_by = request.user
            competition.save()
            return redirect("arena:superadmin_competition_admins", slug=competition.slug)
    else:
        form = CompetitionForm()

    return render(request, "arena/admin/superadmin/competition_form.html", {"form": form})


@superadmin_required
def competition_edit(request, slug):
    competition = get_competition_or_404(slug)
    if request.method == "POST":
        form = CompetitionForm(request.POST, instance=competition)
        if form.is_valid():
            form.save()
            return redirect("arena:superadmin_competitions")
    else:
        form = CompetitionForm(instance=competition)

    return render(
        request, "arena/admin/superadmin/competition_form.html", {"form": form, "competition": competition}
    )


@superadmin_required
def competition_admins(request, slug):
    competition = get_competition_or_404(slug)

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(username=email).first()
        if user:
            Membership.objects.update_or_create(
                user=user, competition=competition, defaults={"role": Membership.Role.ADMIN}
            )
        return redirect("arena:superadmin_competition_admins", slug=slug)

    admins = competition.memberships.filter(role=Membership.Role.ADMIN).select_related("user")
    context = {"competition": competition, "admins": admins}
    return render(request, "arena/admin/superadmin/competition_admins.html", context)


@superadmin_required
@require_POST
def remove_admin(request, slug, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, competition__slug=slug, role=Membership.Role.ADMIN)
    membership.role = Membership.Role.PLAYER
    membership.save(update_fields=["role"])
    return redirect("arena:superadmin_competition_admins", slug=slug)
