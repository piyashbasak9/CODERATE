from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('users/', views.UserListView.as_view(), name='users_list'),
    path('user/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('add-problem/', views.AddProblemView.as_view(), name='add_problem'),
    path('problem/<str:problem_id>/', views.ProblemDetailView.as_view(), name='problem_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('rate/<str:problem_id>/', views.RateProblemView.as_view(), name='rate_problem'),
    path('mark/<str:problem_id>/', views.MarkProblemView.as_view(), name='mark_problem'),
]
