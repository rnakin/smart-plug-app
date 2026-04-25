from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from urllib.parse import quote
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.exceptions import TokenError
import datetime
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

# ── Custom Token Types ─────────────────────────────────────────────────────────

class EmailVerifyToken(Token):
    token_type = 'email_verify'
    lifetime = datetime.timedelta(hours=24)


class PasswordResetToken(Token):
    token_type = 'password_reset'
    lifetime = datetime.timedelta(hours=1)


# ── Register ───────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email    = request.data.get('email', '')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not email:
            return Response(
                {'error': 'Email is required for account verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'An account with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_active=False,
        )

        token = EmailVerifyToken.for_user(user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/?token={quote(str(token))}"
        if settings.DEBUG:
            print(f"\n🔗 verification URL: {verify_url}\n")
        send_mail(
            subject='Verify your KnowWatt account',
            message=(
                f'Hi {username},\n\n'
                f'Please verify your email address by clicking the link below:\n\n'
                f'{verify_url}\n\n'
                f'This link expires in 24 hours.\n\n'
                f'— KnowWatt'
            ),
            from_email='noreply@knowwatt.com',
            recipient_list=[email],
            fail_silently=True,
        )

        return Response({
            'message': 'Account created. Please check your email to verify your account.',
        }, status=status.HTTP_201_CREATED)

class ResendVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'error': 'Account already verified.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = EmailVerifyToken.for_user(user)
            verify_url = f"{settings.FRONTEND_URL}/verify-email/?token={quote(str(token))}"

            if settings.DEBUG:
                print(f"\n🔗 Verify URL: {verify_url}\n")

            send_mail(
                subject='Verify your KnowWatt account',
                message=f'Click to verify your email:\n\n{verify_url}',
                from_email='noreply@knowwatt.com',
                recipient_list=[email],
                fail_silently=True,
            )

        except User.DoesNotExist:
            pass  # Don't reveal if email exists

        return Response({'message': 'If that email exists and is unverified, a new link has been sent.'})
# ── Verify Email ───────────────────────────────────────────────────────────────

class VerifyEmailView(APIView):
    def post(self, request):
        token_string = request.data.get('token')

        if not token_string:
            return Response(
                {'error': 'Verification token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = EmailVerifyToken(token_string)
            user = User.objects.get(id=token['user_id'])

            if user.is_active:
                return Response({'message': 'Email already verified. You can log in.'})

            user.is_active = True
            user.save()

            return Response({'message': 'Email verified successfully. You can now log in.'})

        except TokenError:
            return Response(
                {'error': 'Verification link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ── Login ──────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response({
            'access':  response.data['access'],
            'refresh': response.data['refresh'],
        }, status=status.HTTP_200_OK)


# ── Logout ─────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


# ── Refresh ────────────────────────────────────────────────────────────────────

class RefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            return Response({'access': str(token.access_token)}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ── Me ─────────────────────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        })


# ── Update Profile ─────────────────────────────────────────────────────────────

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        username = request.data.get('username')
        email = request.data.get('email')
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
            user.username = username

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
            user.email = email

        if new_password:
            if not current_password:
                return Response({'error': 'Current password is required to set a new password'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(current_password):
                return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)

        user.save()
        return Response({
            'message': 'Profile updated successfully',
            'username': user.username,
            'email': user.email,
        })


# ── Forgot Password ────────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.for_user(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={quote(str(token))}"
            print(f"\n🔗 Reset URL: {reset_url}\n")

            send_mail(
                subject='Reset your KnowWatt password',
                message=f'Click to reset your password:\n\n{reset_url}',
                from_email='noreply@knowwatt.com',
                recipient_list=[email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass

        return Response({'message': 'If that email exists, a reset link has been sent.'})


# ── Reset Password ─────────────────────────────────────────────────────────────

class ResetPasswordView(APIView):
    def post(self, request):
        token_string = request.data.get('token')
        new_password = request.data.get('password')

        if not token_string or not new_password:
            return Response(
                {'error': 'Token and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = PasswordResetToken(token_string)
            user = User.objects.get(id=token['user_id'])
            user.set_password(new_password)
            user.save()
            # token.blacklist()

            return Response({'message': 'Password reset successful. You can now login.'})

        except TokenError:
            return Response(
                {'error': 'Reset link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ── Session-based Authentication Views (Django Templates) ─────────────────────────

class SessionLoginView(AuthLoginView):
    template_name = 'login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/home/'


class SessionLogoutView(AuthLogoutView):
    next_page = '/login/'


class SessionRegisterView(TemplateView):
    template_name = 'register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/home/')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')

        if not username or not password:
            return render(request, self.template_name, {'error': 'Username and password are required'})

        if not email:
            return render(request, self.template_name, {'error': 'Email is required for account verification'})

        if User.objects.filter(username=username).exists():
            return render(request, self.template_name, {'error': 'Username already exists'})

        if User.objects.filter(email=email).exists():
            return render(request, self.template_name, {'error': 'An account with this email already exists'})

        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, self.template_name, {'error': ', '.join(e.messages)})

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_active=False,
        )

        token = EmailVerifyToken.for_user(user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/?token={quote(str(token))}"
        if settings.DEBUG:
            print(f"\n🔗 verification URL: {verify_url}\n")
        send_mail(
            subject='Verify your KnowWatt account',
            message=(
                f'Hi {username},\n\n'
                f'Please verify your email address by clicking the link below:\n\n'
                f'{verify_url}\n\n'
                f'This link expires in 24 hours.\n\n'
                f'— KnowWatt'
            ),
            from_email='noreply@knowwatt.com',
            recipient_list=[email],
            fail_silently=True,
        )

        # Auto-login after registration (optional, but requires email verification usually)
        # For now, redirect to login page with success message
        return redirect('/login/')


class SessionForgotPasswordView(TemplateView):
    template_name = 'forgot_password.html'

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if not email:
            return render(request, self.template_name, {'error': 'Email is required'})

        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.for_user(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={quote(str(token))}"
            print(f"\n🔗 Reset URL: {reset_url}\n")

            send_mail(
                subject='Reset your KnowWatt password',
                message=f'Click to reset your password:\n\n{reset_url}',
                from_email='noreply@knowwatt.com',
                recipient_list=[email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass

        return render(request, self.template_name, {'message': 'If that email exists, a reset link has been sent.'})


class SessionResetPasswordView(TemplateView):
    template_name = 'reset_password.html'

    def post(self, request, *args, **kwargs):
        token_string = request.POST.get('token')
        new_password = request.POST.get('password')

        if not token_string or not new_password:
            return render(request, self.template_name, {'error': 'Token and password are required'})

        try:
            token = PasswordResetToken(token_string)
            user = User.objects.get(id=token['user_id'])
            user.set_password(new_password)
            user.save()

            return render(request, self.template_name, {'message': 'Password reset successful. You can now login.'})

        except TokenError:
            return render(request, self.template_name, {'error': 'Reset link is invalid or expired.'})
        except User.DoesNotExist:
            return render(request, self.template_name, {'error': 'User not found.'})


class SessionVerifyEmailView(TemplateView):
    template_name = 'verify_email.html'

    def get(self, request, *args, **kwargs):
        token_string = request.GET.get('token')
        if not token_string:
            return render(request, self.template_name, {'error': 'Verification token is required'})

        try:
            token = EmailVerifyToken(token_string)
            user = User.objects.get(id=token['user_id'])

            if user.is_active:
                return render(request, self.template_name, {'message': 'Email already verified. You can log in.'})

            user.is_active = True
            user.save()

            return render(request, self.template_name, {'message': 'Email verified successfully. You can now log in.'})

        except TokenError:
            return render(request, self.template_name, {'error': 'Verification link is invalid or expired.'})
        except User.DoesNotExist:
            return render(request, self.template_name, {'error': 'User not found.'})


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class SessionDashboardView(TemplateView):
    template_name = 'home/app.html'