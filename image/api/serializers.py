from django.contrib.auth.models import User
from rest_framework import serializers

from authentication.models import Profile
from image.models import Category, Item, Author, Software


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']
        read_only_fields = fields

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []


class ProfileSerializer(serializers.ModelSerializer):
    # image = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['id', 'nickname', 'avatar']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'profile']


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Author
        fields = '__all__'


class SoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Software
        fields = ['id', 'name', 'description']

class ItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    author = AuthorSerializer()
    software = SoftwareSerializer()

    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['reviewed_at', 'created_at', 'updated_at']
