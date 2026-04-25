
from django.contrib import admin
from django.urls import path,include
from account.views import SessionLoginView, SessionLogoutView, SessionRegisterView, SessionForgotPasswordView, SessionResetPasswordView, SessionVerifyEmailView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Session-based authentication views (Django Templates)
    path('login/', SessionLoginView.as_view(), name='login'),
    path('logout/', SessionLogoutView.as_view(), name='logout'),
    path('register/', SessionRegisterView.as_view(), name='register'),
    path('forgot-password/', SessionForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', SessionResetPasswordView.as_view(), name='reset_password'),
    path('verify-email/', SessionVerifyEmailView.as_view(), name='verify_email'),
    
    # Keep API endpoints under /auth/ (or /api/auth/)
    path("auth/", include("account.urls")),
    
    # Main app pages
    path("", include("funt.urls")),
    
    # API endpoints
    path("api/houses/", include("house.urls")),
    path("api/", include("device.urls")),
    path("api/", include("alert.urls")),
]
