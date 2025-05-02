from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from apps.accounts.models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_profile_creation(self):
        """Test that profile is created automatically for new users"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertFalse(self.user.profile.is_admin)
        self.assertIsNone(self.user.profile.yandex_id)

    def test_profile_str_method(self):
        """Test the string representation of UserProfile"""
        expected_str = "testuser's profile"
        self.assertEqual(str(self.user.profile), expected_str)

    def test_profile_update(self):
        """Test updating profile attributes"""
        self.user.profile.is_admin = True
        self.user.profile.yandex_id = 'test_yandex_id'
        self.user.profile.save()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        self.assertTrue(self.user.profile.is_admin)
        self.assertEqual(self.user.profile.yandex_id, 'test_yandex_id')

    def test_user_delete_cascades_to_profile(self):
        """Test that deleting a user also deletes the associated profile"""
        profile_id = self.user.profile.id
        profile_count_before = UserProfile.objects.count()
        
        # Delete the user
        self.user.delete()
        
        # Check that profile was also deleted
        profile_count_after = UserProfile.objects.count()
        self.assertEqual(profile_count_before - 1, profile_count_after)
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')
        
    def test_profile_view(self):
        """Test that a user can view their profile page"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertContains(response, 'testuser')


class RegistrationViewTest(TestCase):
    def test_registration_view_get(self):
        """Test accessing the registration page"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        
    def test_registration_view_post(self):
        """Test user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex-password123',
            'password2': 'complex-password123',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify user was created
        self.assertTrue(
            User.objects.filter(username='newuser').exists()
        )
        
        # Verify profile was created
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
    def test_login_view_get(self):
        """Test accessing the login page"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        
    def test_login_view_post_success(self):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpassword',
        }
        response = self.client.post(reverse('accounts:login'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
    def test_login_view_post_failure(self):
        """Test failed login attempt"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(reverse('accounts:login'), data)
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(
            response, 
            'Please enter a correct username and password'
        )
