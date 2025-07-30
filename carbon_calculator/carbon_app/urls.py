from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('home/', views.home, name='home'), 
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('group/create/', views.group_create, name='group_create'),
    path('group/join/', views.group_join, name='group_join'),
    path('previous_scores/', views.previous_scores, name='previous_scores'),
    path('logout/', views.user_logout, name='account_logout'),
    
]