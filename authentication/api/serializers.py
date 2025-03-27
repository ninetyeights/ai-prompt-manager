from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime, timezone
from rest_framework_simplejwt.settings import api_settings

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        access_token_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        refresh_token_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

        data['access_token_expiry'] = int((datetime.now(timezone.utc) + access_token_lifetime).timestamp() * 1000)
        data['refresh_token_expiry'] = int((datetime.now(timezone.utc) + refresh_token_lifetime).timestamp() * 1000)

        data['is_superuser'] = self.user.is_superuser
        data['is_staff'] = self.user.is_staff
        data['nickname'] = self.user.profile.nickname
        data['avatar'] = self.user.profile.avatar.url
        return data
