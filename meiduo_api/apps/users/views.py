from rest_framework.views import APIView
from .models import User
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from .serializers import UserCreateSerializer


class UserCountView(APIView):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        if count > 0:
            raise serializers.ValidationError("用户名已经存在")
        return Response({
            'username': username,
            'count': count
        })


class MobileCountView(APIView):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        if count > 0:
            raise serializers.ValidationError("手机号已被占用")
        return Response({
            'mobile': mobile,
            'count': count
        })


class UserCreateView(CreateAPIView):
    serializer_class = UserCreateSerializer
