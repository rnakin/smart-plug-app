from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

# ── Register ───────────────────────────────────────────────────────────────────

class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        email    = request.POST.get('email', '')

        if not username or not password:
            return render(request, 'register.html', {'error': 'Fields required'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username exists'})

        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'register.html', {'error': e.messages})
        
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # Log the user in immediately
        login(request, user)
        return redirect('/home/')

# ── Login & Logout ─────────────────────────────────────────────────────────────

# Uses standard Django LoginView
class LoginView(AuthLoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

def LogoutView(request):
    logout(request)
    return redirect('login')  # เปลี่ยนเป็นชื่อหน้า Login ของคุณ

# ── Profile Management ─────────────────────────────────────────────────────────

class MeView(View):
    # If this is an API endpoint for an SPA, keep it as APIView, otherwise standard View
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not logged in'}, status=401)
        
        return JsonResponse({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        })

class UpdateProfileView(View):
    @method_decorator(login_required)
    def post(self, request):
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        # ... validation logic ...
        user.username = username
        user.email = email
        user.save()
        return redirect('/profile/')

# ── Password Reset (Secure Django Standard) ────────────────────────────────────

class ForgotPasswordView(View):
    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            # Send email...
        except User.DoesNotExist:
            pass
        return render(request, 'forgot_password.html', {'message': 'Check your email.'})

class ResetPasswordView(View):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            new_password = request.POST.get('password')
            user.set_password(new_password)
            user.save()
            return redirect('/login/')
        
        return HttpResponseBadRequest("Invalid link")