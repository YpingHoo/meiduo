from rest_framework.views import APIView
from .models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from .serializers import UserCreateSerializer, UserDetailSerializer, EmailSerializer, ChangePasswordSerializer
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated


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


class UserDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEamilView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            raise Response({"message": "缺少token"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.check_verify_email_token(token)
        if user is None:
            raise Response({"message": "链接信息无效"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({"message": "ok"})


class ChangePasswordView(RetrieveUpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
