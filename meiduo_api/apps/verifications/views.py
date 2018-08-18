from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework import serializers
import random
from utils.ytx_sdk.sendSMS import CCP


# Create your views here.
class SMSCodeView(APIView):
    def get(self, request, mobile):
        redis_cli = get_redis_connection('verify_code')

        sms_flag = redis_cli.get('sms_flag_' + mobile)
        if sms_flag:
            raise serializers.ValidationError("请勿重复发送")

        sms_code = str(random.randint(100000, 999999))
        redis_pl = redis_cli.pipeline()
        redis_pl.setex('sms_code_' + mobile, 300, sms_code)
        redis_pl.setex('sms_flag_' + mobile, 60, 1)
        redis_pl.ececute()

        # CCP.sendTemplateSMS(mobile, sms_code, 5, 1)
        print(sms_code)

        return Response({'message': 'ok'})
