import os

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Competition, Game, Membership, Prediction, Round, Team


def result_choices(game):
    return [
        (Prediction.Result.NONE, "No selection yet"),
        (Prediction.Result.TEAM1, f"{game.team1.name} win by"),
        (Prediction.Result.TEAM2, f"{game.team2.name} win by"),
        (Prediction.Result.DRAW, "Draw"),
    ]


class PickForm(forms.ModelForm):
    """A player's pick for one game. Used for both the player pick form and the
    competition-admin's game-edit screen - the only difference is which fields
    the surrounding view/template lets the user touch (admins also see `override`)."""

    class Meta:
        model = Prediction
        fields = ["result", "spread"]
        widgets = {
            "spread": forms.NumberInput(attrs={"size": 3, "min": 0}),
            "result": forms.Select(attrs={"onchange": "resultCheck(this)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["result"] = forms.ChoiceField(
            choices=result_choices(self.instance.game),
            widget=forms.Select(attrs={"onchange": "resultCheck(this)"}),
        )


class AdminPickForm(PickForm):
    class Meta(PickForm.Meta):
        fields = ["result", "spread", "override"]


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ["gamedate", "score1", "score2", "finished"]
        widgets = {
            "score1": forms.NumberInput(attrs={"size": 3, "min": 0}),
            "score2": forms.NumberInput(attrs={"size": 3, "min": 0}),
        }


class GameCreateForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ["team1", "team2", "gamedate"]

    def __init__(self, *args, competition=None, **kwargs):
        super().__init__(*args, **kwargs)
        if competition is not None:
            self.fields["team1"].queryset = competition.teams.all()
            self.fields["team2"].queryset = competition.teams.all()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("team1") and cleaned_data.get("team1") == cleaned_data.get("team2"):
            raise ValidationError("A team cannot play itself")
        return cleaned_data


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "descr", "pool", "code"]


class RoundForm(forms.ModelForm):
    class Meta:
        model = Round
        fields = ["name", "order", "start", "finish", "entry_fee"]


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = [
            "name", "slug", "description", "kind", "status", "visibility",
            "start_date", "end_date", "default_entry_fee", "scoring_rules",
        ]
        widgets = {"scoring_rules": forms.Textarea(attrs={"rows": 20, "class": "code-editor"})}


class MembershipRoleForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["role", "blocked"]


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class AdminMembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["phone_number", "blocked"]


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="First name", min_length=2, max_length=30)
    last_name = forms.CharField(label="Surname", min_length=2, max_length=30)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, request):
        base_url = os.getenv("ARENA_WEB_BASE_URL", "http://localhost")
        user = User.objects.create_user(
            self.cleaned_data["email"], self.cleaned_data["email"], self.cleaned_data["password1"]
        )
        user.is_active = False
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()

        context = {
            "request": request,
            "protocol": request.scheme,
            "username": user.email,
            "domain": request.META["HTTP_HOST"],
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
            "email": user.email,
            "base_url": base_url,
            "user": user,
        }
        subject = render_to_string("accounts/email/activation_subject.txt", context)
        body = render_to_string("accounts/email/activation_email.txt", context)
        html_body = render_to_string("accounts/email/activation_email.html", context)
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_body)

        return user
