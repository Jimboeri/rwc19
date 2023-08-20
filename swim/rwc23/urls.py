from django.urls import path, include
#from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name='rwc23'
urlpatterns = [
    path('', views.currRound, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('pickupdate/<int:rnd_id>/', views.makePicks, name='pickUpdate'),
    path('player/<int:player_id>/', views.playerDets, name='playerDets'),
    path('game/edit/<int:game_id>/', views.gameEdit, name='gameEdit'),
    path('game/view/<int:game_id>/', views.gameView, name='gameView'),
    path('about/', views.about, name='about'),
    path('email_results/<int:game_id>/', views.email_results, name='email_results'),
    path('pointsView/<int:pick_id>/', views.pointsView, name='pointsView'),
    path('otherrounds/', views.otherRounds, name='otherRounds'),
    path('disprounds/<int:player_id>/<int:round_id>/', views.dispRound, name='dispRound'),

    # Admin functions
    path('admin/general/', views.adminGeneral, name='adminGeneral'),

    # User management URL's    
    path("logout/", views.logout, name="logout"),
    path("login/", views.login, name="login"),
        path("signup/", views.signup, name="signup"),
    path(
        "activate/(<uidb64>[0-9A-Za-z_\-]+)/(<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/",
        views.activate_account,
        name="activate",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/email/password_reset_email.txt",
            subject_template_name="accounts/email/password_reset_subject.txt",
            success_url='password_reset_done',
        ),
        name="password_reset",
    ),

    path(
        "password-reset/password_reset_done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-confirm/(<uidb64>[0-9A-Za-z_\-]+)/(<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="password_reset_complete",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-confirm/(<uidb64>[0-9A-Za-z_\-]+)/(<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/password_reset_complete",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),


]