from rest_framework import serializers
from rest_framework import viewsets
from rest_framework import permissions
from apis_core.apis_metainfo.models import Uri


class UriSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = Uri
        fields = '__all__'

class UriViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Uri.objects.all()
    serializer_class = UriSerializer
    permission_classes = [permissions.IsAuthenticated]
