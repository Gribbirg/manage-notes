from .models import UserProfile


def save_yandex_id(backend, user, response, *args, **kwargs):
    """
    Pipeline function to save Yandex ID to user profile when user
    authenticates with Yandex OAuth.
    """
    if backend.name == 'yandex-oauth2':
        # Get or create user profile
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
        
        # Save Yandex ID to profile
        user.profile.yandex_id = response.get('id', '')
        user.profile.save()
        
        return {
            'yandex_id': response.get('id', ''),
            'user': user
        } 