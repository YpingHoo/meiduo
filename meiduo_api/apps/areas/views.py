from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Area
from .serializers import AreaSerializer, SubAreaSerializer
from rest_framework_extensions.cache.mixins import CacheResponseMixin


# Create your views here

class AreaModelViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    def get_serializer_class(self):
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer

    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()
