from django.contrib.auth import views as auth_views
from django.urls import path

from .views import admin as admin_views
from .views import auth as auth_views_local
from .views import player, superadmin

app_name = "arena"

urlpatterns = [
    # Player-facing
    path("", player.dashboard, name="dashboard"),
    path("join/<slug:slug>/", player.join, name="join"),
    path("c/<slug:slug>/", player.competition_home, name="competition_home"),
    path("c/<slug:slug>/pickupdate/<int:round_id>/", player.pick_update, name="pick_update"),
    path("c/<slug:slug>/player/<int:user_id>/", player.player_details, name="player_details"),
    path("c/<slug:slug>/game/view/<int:game_id>/", player.game_view, name="game_view"),
    path("c/<slug:slug>/otherrounds/", player.other_rounds, name="other_rounds"),
    path("c/<slug:slug>/disprounds/<int:user_id>/<int:round_id>/", player.disp_round, name="disp_round"),
    path("c/<slug:slug>/pointsview/<int:prediction_id>/", player.points_view, name="points_view"),
    path("c/<slug:slug>/about/", player.about, name="about"),

    # Competition-admin
    path("c/<slug:slug>/admin/teams/", admin_views.team_list, name="admin_teams"),
    path("c/<slug:slug>/admin/teams/<int:team_id>/delete/", admin_views.team_delete, name="admin_team_delete"),
    path("c/<slug:slug>/admin/rounds/", admin_views.round_list, name="admin_rounds"),
    path("c/<slug:slug>/admin/rounds/refresh/", admin_views.refresh_rounds, name="admin_refresh_rounds"),
    path("c/<slug:slug>/admin/rounds/<int:round_id>/games/", admin_views.round_games, name="admin_round_games"),
    path("c/<slug:slug>/admin/game/edit/<int:game_id>/", admin_views.game_edit, name="game_edit"),
    path("c/<slug:slug>/admin/players/", admin_views.player_list, name="admin_players"),
    path("c/<slug:slug>/admin/player/<int:user_id>/", admin_views.player_detail, name="admin_player_detail"),
    path("c/<slug:slug>/admin/player/<int:user_id>/payment/", admin_views.player_payment, name="admin_player_payment"),
    path(
        "c/<slug:slug>/admin/player/<int:user_id>/payment/full/",
        admin_views.player_full_payment,
        name="admin_player_full_payment",
    ),

    # Superadmin
    path("superadmin/competitions/", superadmin.competition_list, name="superadmin_competitions"),
    path("superadmin/competitions/new/", superadmin.competition_create, name="superadmin_competition_create"),
    path("superadmin/competitions/<slug:slug>/edit/", superadmin.competition_edit, name="superadmin_competition_edit"),
    path(
        "superadmin/competitions/<slug:slug>/admins/",
        superadmin.competition_admins,
        name="superadmin_competition_admins",
    ),
    path(
        "superadmin/competitions/<slug:slug>/admins/<int:membership_id>/remove/",
        superadmin.remove_admin,
        name="superadmin_competition_admin_remove",
    ),

    # Auth
    path("signup/", auth_views_local.signup, name="signup"),
    path("signup/done/", auth_views_local.signup_done, name="signup_done"),
    path("activate/<uidb64>/<token>/", auth_views_local.activate_account, name="activate"),
    path("login/", auth_views_local.login, name="login"),
    path("logout/", auth_views_local.logout, name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/email/password_reset_email.txt",
            subject_template_name="accounts/email/password_reset_subject.txt",
            success_url="done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/password-reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
