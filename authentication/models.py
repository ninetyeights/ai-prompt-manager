from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    nickname = models.CharField(max_length=32, verbose_name="昵称")
    avatar = models.ImageField(upload_to="avatars", default="default.jpg")

    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.avatar.path)

        width, height = img.size
        min_dimension = min(width, height)
        left = (width - min_dimension) / 2
        top = (height - min_dimension) / 2
        right = (width + min_dimension) / 2
        bottom = (height + min_dimension) / 2

        img = img.crop((left, top, right, bottom))

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.avatar.path)

    class Meta:
        verbose_name = "个人用户配置"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.nickname} - {self.user.username}"
