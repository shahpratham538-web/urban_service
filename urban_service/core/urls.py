from django.urls import path 
from . import views 

urlpatterns = [
    path('', views.homeView, name="home"),
    path('signup/', views.userSignupView,name="signup"),
    path('login/',views.userLoginView,name="login"),
    path("admin-dashboard/", views.adminDashboardView, name="admin_dashboard"),
    path("provider-dashboard/", views.providerDashboardView, name="provider_dashboard"),
    path("resident-dashboard/", views.residentDashboardView, name="resident_dashboard"),
    path("support-dashboard/", views.supportDashboardView, name="support_dashboard"),
    path("logout/", views.userLogoutView, name="logout"),
]