def competition(request):
    """
    Exposes `competition` and `is_admin` in every template automatically when
    the current view was wrapped by `competition_member_required` or
    `competition_admin_required` (both stash the resolved Competition on
    `request.competition`) - so templates don't need every view to repeat it.
    """
    comp = getattr(request, "competition", None)
    if comp is None:
        return {}
    is_admin = request.user.is_authenticated and comp.is_admin(request.user)
    return {"competition": comp, "is_admin": is_admin}
