from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User, OAuthQQUser
from .utils import OAuthQQ
from django_redis import get_redis_connection


class OAuthQQUserSerializer(serializers.ModelSerializer):
    mobile = serializers.RegexField(regex=r'^1[3-9]\d{9}$', label="手机号")
    sms_code = serializers.CharField(label="短信验证码", write_only=True)
    token = serializers.CharField(read_only=True)
    access_token = serializers.CharField(write_only=True, label="操作凭证")

    class Meta:
        model = User
        fields = ('mobile', 'password', 'username', 'access_token', 'sms_code', 'token', 'id')
        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        access_token = attrs.get('access_token')
        openid = OAuthQQ.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError("无效的access_token")

        attrs['openid'] = openid

        mobile = attrs.get('mobile')
        sms_code = attrs.get('sms_code')
        redis_cli = get_redis_connection('verify_code')
        key = 'sms_code_' + mobile
        sms_code_redis = redis_cli.get(key)
        if not sms_code_redis:
            raise serializers.ValidationError("验证码失效")
        if sms_code_redis.decode() != sms_code:
            raise serializers.ValidationError("验证码错误")

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs.get('password')
            if not user.check_password(password):
                raise serializers.ValidationError("密码错误")
            attrs['user'] = user

        return attrs

    def create(self, validated_data):
        openid = validated_data.get("openid")
        mobile = validated_data.get("mobile")
        user = validated_data.get("user")
        password = validated_data.get("password")

        if not user:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

        OAuthQQUser.objects.create(user=user, openid=openid)

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return user
