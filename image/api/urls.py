from rest_framework.routers import DefaultRouter

from image.api.views import CategoryViewSet, ItemViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'latest', ItemViewSet, basename='latest')

urlpatterns = router.urls