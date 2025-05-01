from social_core.backends.yandex import YandexOAuth2
from .models import UserProfile


class CustomYandexOAuth2(YandexOAuth2):
    """Extended Yandex OAuth2 backend to store Yandex ID in user profile."""
    
    def get_user_details(self, response):
        """Return user details from Yandex account."""
        user_details = super().get_user_details(response)
        return user_details
    
    def pipeline(self, pipeline, pipeline_index=0, *args, **kwargs):
        """Custom pipeline to store Yandex ID in user profile."""
        if 'user' in kwargs:
            user = kwargs['user']
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(user=user)
            
            user.profile.yandex_id = kwargs.get('uid', '')
            user.profile.save()
        
        return super().pipeline(pipeline, pipeline_index, *args, **kwargs) 