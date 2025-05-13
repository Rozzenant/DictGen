from django.contrib.auth.backends import BaseBackend
from .models import User

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Пытаемся найти пользователя по username или email
            user = User.objects.filter(username=username).first() or \
                   User.objects.filter(email=username).first()
            
            if user and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 