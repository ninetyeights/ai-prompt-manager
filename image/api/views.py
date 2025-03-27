from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from image.models import Category, Item
from .serializers import CategorySerializer, ItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.prefetch_related('subcategories').all()
    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ItemViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Item.objects.all().order_by('-created_at')
    serializer_class = ItemSerializer
