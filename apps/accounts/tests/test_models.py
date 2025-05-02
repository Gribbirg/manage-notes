from django.test import TestCase
from django.contrib.auth.models import User
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