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
    #path('gateway/<int:gateway_ref>/', views.gatewayDetail, name='gatewayDetail'),
    #path('node/update/<int:node_ref>/', views.nodeUpdate, name='nodeUpdate'),
    #path('node/modupdate/<int:node_ref>/', views.nodeModNotify, name='nodeModNotify'),
]