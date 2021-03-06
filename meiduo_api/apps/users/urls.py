from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UserCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^users/$', views.UserCreateView.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'^emails/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.VerifyEamilView.as_view()),
]

router = DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls
