from django.urls import path
from .views import delete_item

from . import views

app_name = "image"

urlpatterns = [
    path('update-copy-count/<int:pk>', views.update_copy_count, name="update_copy_count"),
    path('update-view-count/<int:pk>', views.update_view_count, name="update_view_count"),
    path('category/<int:pk>', views.category, name="category"),
    path('delete-item/<int:pk>/', delete_item, name='delete_item'),
    path('update-item/<int:pk>', views.update_item, name='update_item'),
    path('approve-item/<int:pk>', views.approve_item, name='approve_item'),
    path('reject-item/<int:pk>', views.reject_item, name='reject_item'),
    path('add/', views.update_item, name='add'),
]
