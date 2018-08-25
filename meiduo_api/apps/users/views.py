from rest_framework.views import APIView
from .models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from .serializers import UserCreateSerializer, UserDetailSerializer, EmailSerializer, ChangePasswordSerializer
from .serializers import AddressTitleSerializer, UserAddressSerializer
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from . import constants
from rest_framework.decorators import action


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


class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        address = self.get_object()

        address.is_deleted = True
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)




