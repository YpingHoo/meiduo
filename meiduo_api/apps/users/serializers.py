import re
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from .models import User, Address
from django_redis import get_redis_connection
from celery_tasks.email.tasks import send_verify_email


class UserCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(min_length=5,
                                     max_length=20,
                                     error_messages={
                                         'min_length': '用户名为5-20个字符',
                                         'max_length': '用户名为5-20个字符'
                                     })
    password = serializers.CharField(min_length=8,
                                     max_length=20,
                                     write_only=True,
                                     error_messages={
                                         'min_length': '密码为8-20个字符',
                                         'max_length': '密码为8-20个字符',
                                     })

    password2 = serializers.CharField(min_length=8,
                                      max_length=20,
                                      write_only=True,
                                      error_messages={
                                          'min_length': '密码为8-20个字符',
                                          'max_length': '密码为8-20个字符',
                                      })

    mobile = serializers.CharField()
    sms_code = serializers.CharField(write_only=True)
    allow = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate_username(self, value):
        count = User.objects.filter(username=value).count()
        if count > 0:
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError("两次输入的密码不一致")

        redis_cli = get_redis_connection('verify_code')
        key = 'sms_code_' + attrs.get('mobile')
        sms_code_redis = redis_cli.get(key)
        if not sms_code_redis:
            raise serializers.ValidationError("验证码无效")
        redis_cli.delete(key)
        sms_code_request = attrs.get('sms_code')
        if sms_code_redis.decode() != sms_code_request:
            raise serializers.ValidationError("验证码输入有误")

        return attrs

    def validate_mobile(self, value):
        count = User.objects.filter(mobile=value).count()
        if count > 0:
            raise serializers.ValidationError("手机号被占用")
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("手机号格式错误")
        return value

    def validate_sms_code(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("验证码错误")
        return value

    def validate_allow(self, value):
        if not value:
            raise serializers.ValidationError("请勾选同意协议")
        return value

    def create(self, validated_data):
        user = User()
        user.username = validated_data.get('username')
        user.set_password(validated_data.get('password'))
        user.mobile = validated_data.get('mobile')
        user.save()

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            'email': {
                'required': True,
            }
        }

    def update(self, instance, validated_data):
        email = validated_data.get('email')
        instance.email = email
        instance.save()

        verify_url = instance.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    password = serializers.CharField(read_only=True,
                                     min_length=8,
                                     max_length=20,
                                     error_messages={
                                         'min_length': "密码必须8-20个字符",
                                         'max_length': "密码必须8-20个字符",
                                     })
    password1 = serializers.CharField(write_only=True,
                                      min_length=8,
                                      max_length=20,
                                      error_messages={
                                          'min_length': "密码必须8-20个字符",
                                          'max_length': "密码必须8-20个字符",
                                      })
    password2 = serializers.CharField(write_only=True,
                                      min_length=8,
                                      max_length=20,
                                      error_messages={
                                          'min_length': "密码必须8-20个字符",
                                          'max_length': "密码必须8-20个字符",
                                      })

    def validate(self, attrs):
        user = self.context['request'].user
        password = attrs.get("password")
        if not user.check_password(password):
            raise serializers.ValidationError("原密码错误")

        password1 = attrs.get("password1")
        password2 = attrs.get("password2")
        if password1 != password2:
            raise serializers.ValidationError("新密码两次输入不一致")

        return attrs

    def update(self, instance, validated_data):
        password = validated_data.get('password1')
        instance.set_password(password)
        instance.save()
        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label="省ID", required=True)
    city_id = serializers.IntegerField(label="市ID", required=True)
    district_id = serializers.IntegerField(label="区ID", required=True)

    class Meta:
        model = Address
        exclude = ['user', 'is_deleted', 'create_datetime', 'update_datetime']

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)