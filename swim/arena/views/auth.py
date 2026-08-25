from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from ..forms import SignupForm


def login(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "arena:dashboard"

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect(next_url)
        messages.error(request, "Wrong username or password")

    return render(request, "accounts/login.html", {"next": next_url})


def logout(request):
    auth.logout(request)
    return render(request, "accounts/logout.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("arena:dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save(request)
            messages.success(request, "Account created, please check your email")
            return redirect("arena:signup_done")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def signup_done(request):
    return render(request, "accounts/signup_done.html")


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.info(request, "Account activated. Please log in.")
    else:
        messages.info(request, "Link expired. Contact an administrator to activate your account.")

    return redirect("arena:login")
