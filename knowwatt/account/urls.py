from django.urls import path
from . import views

urlpatterns = [
    # ── Authentication Pages (Templates) ──
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    # path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),

    # ── API Endpoints (For AJAX/Fetch/HTMX requests using  Auth) ──
    # Note: These views should use permission_classes = [IsAuthenticated] 
    # and support  auth automatically.
    path('api/me/', views.MeView.as_view(), name='api_me'),
    path('api/me/update/', views.UpdateProfileView.as_view(), name='api_update_profile'),
    
    # # ── Dashboard ──
    # path('home/', views.DashboardView.as_view(), name='home'),
]