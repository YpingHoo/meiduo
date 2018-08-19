import re
from rest_framework import serializers
from .models import User
from django_redis import get_redis_connection


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

    def create(self, validated_data):
        user = User()
        user.username = validated_data.get('username')
        user.set_password(validated_data.get('password'))
        user.mobile = validated_data.get('mobile')
        user.save()
        return user
