from django import forms
from .models import Prediction, Game
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

from . import models

import os

def gameResult(inGame):
    aChoice = []
    aChoice.append((0, f"No selection yet "))
    aChoice.append((1, f"{inGame.Team1.teamID} win by "))
    aChoice.append((2, f"{inGame.Team2.teamID} win by "))
    aChoice.append((3, "Draw"))
    return(aChoice)


class PickDetailForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['spread', 'result']
        widgets = {
            'spread': forms.TextInput(attrs={'size': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(PickDetailForm, self).__init__(*args, **kwargs)
        #logging.debug(f"PickDetailForm instance: {self.instance}")
        self.fields['result'] = forms.ChoiceField(choices=gameResult(self.instance.game))


class PickAdminDetailForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['spread', 'result']
        widgets = {
            'spread': forms.TextInput(attrs={'size': 3}),
        }
    def __init__(self, *args, **kwargs):
        super(PickAdminDetailForm, self).__init__(*args, **kwargs)
        self.fields['result'] = forms.ChoiceField(choices=gameResult(self.instance.game), help_text="xxx",)


class gameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['score1', 'score2', 'finished']
        widgets = {
            'score1': forms.TextInput(attrs={'size': 3}),
            'score2': forms.TextInput(attrs={'size': 3}),
        }

class CustomUserCreationForm(forms.Form):

    #username = forms.CharField(label="Enter Username", min_length=4, max_length=150)
    email = forms.EmailField(label="Enter email")
    first_name = forms.CharField(label="Enter first name", min_length=2, max_length=30)
    last_name = forms.CharField(label="Enter surname", min_length=2, max_length=30)
    password1 = forms.CharField(
        label="Enter password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput)

    # def clean_username(self):
    #    username = self.cleaned_data["username"].lower()
    #    r = User.objects.filter(username=username)
    #    if r.count():
    #        raise ValidationError("Username already exists")
    #    return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        r = User.objects.filter(username=email)
        if r.count():
            raise ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")

        return password2

    def save(self, request):
        eWeb_Base_URL = os.getenv(
            "RWC23_WEB_BASE_URL", "http://rwc23.west.net.nz")
        user = User.objects.create_user(
            # self.cleaned_data["username"],
            self.cleaned_data["email"],
            self.cleaned_data["email"],
            self.cleaned_data["password1"],
        )
        user.is_active = False
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()

        context = {
            # 'from_email': settings.DEFAULT_FROM_EMAIL,
            'request': request,
            'protocol': request.scheme,
            'username': self.cleaned_data.get('email'),
            'domain': request.META['HTTP_HOST'],
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'email': user.email,
            'base_url': eWeb_Base_URL,
            'user': user,
        }

        subject = render_to_string(
            'accounts/email/activation_subject.txt', context)
        email = render_to_string(
            'accounts/email/activation_email.txt', context)
        html_msg = render_to_string(
            'accounts/email/activation_email.html', context)

        #msg = models.Message(beek=user, subject=subject,
        #                     body=email, html=html_msg)
        #msg.save()

        #send_mail(subject, email, settings.DEFAULT_FROM_EMAIL, [user.email])
        send_mail(subject, email, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_msg)

        return user

class adminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class adminProfileForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ['phoneNumber', 'blocked']

class adminPlayerRoundForm(forms.ModelForm):
    class Meta:
        model = models.PlayerRound
        fields = ['paid', 'paidAmount']
