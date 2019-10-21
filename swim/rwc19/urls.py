from django.urls import path, include
from django.conf.urls import url

from . import views

app_name='rwc19'
urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('pickupdate/', views.makePicks, name='pickUpdate'),
    path('player/<int:player_id>/', views.playerDets, name='playerDets'),
    path('game/edit/<int:game_id>/', views.gameEdit, name='gameEdit'),
    path('game/view/<int:game_id>/', views.gameView, name='gameView'),
    path('about/', views.about, name='about'),
    path('email_results/<int:game_id>/', views.email_results, name='email_results'),
    path('pointsView/<int:pick_id>/', views.pointsView, name='pointsView'),
]