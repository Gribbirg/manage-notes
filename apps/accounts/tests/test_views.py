from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


class AccountViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_view_post(self):
        """Test register view POST request"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }
        response = self.client.post(self.register_url, user_data)
        
        # Check redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Check that user was created
        self.assertTrue(
            User.objects.filter(username='newuser').exists()
        )
        
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        
    def test_login_view_post_success(self):
        """Test login view POST request with correct credentials"""
        login_data = {
            'username': 'testuser',
            'password': 'testpassword',
        }
        response = self.client.post(self.login_url, login_data)
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # Check that user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
    def test_login_view_post_failure(self):
        """Test login view POST request with incorrect credentials"""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, login_data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        
        # Check that user is not logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
    def test_logout_view(self):
        """Test logout view"""
        # Login first
        self.client.login(username='testuser', password='testpassword')
        
        # Then logout
        response = self.client.get(self.logout_url)
        
        # Should redirect after logout
        self.assertEqual(response.status_code, 302)
        
        # Check that user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.profile_url)
        
        # Should be accessible
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        
    def test_profile_view_unauthenticated(self):
        """Test profile view for unauthenticated user"""
        response = self.client.get(self.profile_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url) 