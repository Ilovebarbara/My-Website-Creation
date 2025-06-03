from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('projects/', views.project_list, name='project_list'),
    path('tutorials/', views.tutorial_list, name='tutorial_list'),
    path('search/', views.search, name='search'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/edit/<int:pk>/', views.edit_post, name='edit_post'),
    path('post/delete/<int:pk>/', views.delete_post, name='delete_post'),
    path('post/toggle-featured/<int:pk>/', views.toggle_featured, name='toggle_featured'),    path('post/like/', views.like_post, name='like_post'),
    path('post/comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('follow/', views.follow_toggle, name='follow_toggle'),
    path('notifications/', views.notifications, name='notifications'),
]
