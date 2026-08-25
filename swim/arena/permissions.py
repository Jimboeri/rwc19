from functools import wraps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from .models import Competition, Membership


def get_competition_or_404(slug):
    return get_object_or_404(Competition, slug=slug)


def competition_admin_required(view_func):
    """
    Requires the logged-in user to be a superuser or an unblocked ADMIN
    member of the competition identified by the `slug` URL kwarg.
    """
    @wraps(view_func)
    @login_required(login_url="arena:login")
    def wrapper(request, *args, **kwargs):
        competition = get_competition_or_404(kwargs["slug"])
        if not competition.is_admin(request.user):
            return HttpResponseForbidden("You do not administer this competition.")
        request.competition = competition
        return view_func(request, *args, **kwargs)

    return wrapper


def competition_member_required(view_func):
    """
    Requires the logged-in user to be a member (admin or player) of the
    competition identified by the `slug` URL kwarg. If they aren't a member
    yet and the competition is public/open, send them to the join page
    instead of a bare 403.
    """
    @wraps(view_func)
    @login_required(login_url="arena:login")
    def wrapper(request, *args, **kwargs):
        competition = get_competition_or_404(kwargs["slug"])
        if not competition.is_member(request.user):
            if competition.visibility == Competition.Visibility.PUBLIC:
                return redirect("arena:join", slug=competition.slug)
            return HttpResponseForbidden("You are not a member of this competition.")
        request.competition = competition
        return view_func(request, *args, **kwargs)

    return wrapper


superadmin_required = user_passes_test(lambda user: user.is_superuser, login_url="arena:login")
