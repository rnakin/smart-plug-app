from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail

class SessionAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_login_success(self):
        """Test successful login creates session"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_failure(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_register_page_loads(self):
        """Test that register page loads correctly"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create account')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newuser', is_active=True).exists())

    def test_register_existing_username(self):
        """Test registration with existing username fails"""
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password': 'newpass123',
            'email': 'another@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already exists')

    def test_register_existing_email(self):
        """Test registration with existing email fails"""
        response = self.client.post(reverse('register'), {
            'username': 'anotheruser',
            'password': 'newpass123',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email already exists')

    def test_forgot_password_page_loads(self):
        """Test that forgot password page loads correctly"""
        response = self.client.get(reverse('forgot_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset password')

    def test_forgot_password_submit(self):
        """Test forgot password form submission and email queuing"""
        response = self.client.post(reverse('forgot_password'), {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'If that email exists, a reset link has been sent')
        
        # Verify email was actually sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset your KnowWatt password', mail.outbox[0].subject)

    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        response = self.client.post(reverse('forgot_password'), {
            'email': 'nonexistent@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'If that email exists, a reset link has been sent')
        # Ensure no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_email_page_loads(self):
        """Test that verify email page loads"""
        response = self.client.get(reverse('verify_email'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email verification is currently disabled.')

    def test_protected_page_requires_login(self):
        """Test that protected pages redirect to login"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        # Using f-string to reconstruct the expected redirect URL with 'next' parameter
        expected_url = f"{reverse('login')}?next={reverse('home')}"
        self.assertRedirects(response, expected_url)

    def test_protected_page_accessible_when_logged_in(self):
        """Test that protected pages are accessible when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class DashboardTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_dashboard_redirects_when_not_logged_in(self):
        """Test dashboard redirects to login when not authenticated"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        expected_url = f"{reverse('login')}?next={reverse('home')}"
        self.assertRedirects(response, expected_url)

    def test_dashboard_accessible_when_logged_in(self):
        """Test dashboard loads when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'KnowWatt')