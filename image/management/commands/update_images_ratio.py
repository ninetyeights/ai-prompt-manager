import os
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from image.models import Image


class Command(BaseCommand):
    help = "更新图片比例"

    def handle(self, *args, **options):
        images = Image.objects.all()

        for image in images:
            print(image)