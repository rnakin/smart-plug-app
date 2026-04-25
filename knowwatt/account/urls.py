# auth/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # API Endpoints (Keep existing JWT-based API endpoints)
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('api/logout/', views.LogoutView.as_view(), name='api_logout'),
    path('api/refresh/', views.RefreshView.as_view(), name='api_refresh'),
    path('api/me/', views.MeView.as_view(), name='api_me'),
    path('api/me/update/', views.UpdateProfileView.as_view(), name='api_update_profile'),
    path('api/forgot-password/', views.ForgotPasswordView.as_view(), name='api_forgot_password'),
    path('api/reset-password/', views.ResetPasswordView.as_view(), name='api_reset_password'),
    path('api/verify-email/', views.VerifyEmailView.as_view(), name='api_verify_email'),
    path('api/resend-verification/', views.ResendVerificationView.as_view(), name='api_resend_verification'),
]
