from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.homeView, name="home"),
    path('signup/', views.userSignupView, name="signup"),
    path('login/', views.userLoginView, name="login"),
    path("admin-dashboard/", views.adminDashboardView, name="admin_dashboard"),
    path("provider-dashboard/", views.providerDashboardView, name="provider_dashboard"),
    path("resident-dashboard/", views.residentDashboardView, name="resident_dashboard"),
    path("support-dashboard/", views.supportDashboardView, name="support_dashboard"),
    path("logout/", views.userLogoutView, name="logout"),

    # ---------- Password Reset ----------
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="core/password_reset_form.html",
        email_template_name="core/password_reset_email.html",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="core/password_reset_done.html",
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="core/password_reset_confirm.html",
        success_url="/reset/complete/",
    ), name="password_reset_confirm"),
    path("reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="core/password_reset_complete.html",
    ), name="password_reset_complete"),
]