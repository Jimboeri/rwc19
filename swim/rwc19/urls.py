from django.urls import path, include
from django.conf.urls import url

from . import views

app_name='rwc19'
urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    #path('', views.IndexView.as_view(), name='index'),
    #path('node/<int:node_ref>/', views.nodeDetail, name='nodeDetail'),
    #path('gateway/<int:gateway_ref>/', views.gatewayDetail, name='gatewayDetail'),
    #path('node/update/<int:node_ref>/', views.nodeUpdate, name='nodeUpdate'),
    #path('node/modupdate/<int:node_ref>/', views.nodeModNotify, name='nodeModNotify'),
]