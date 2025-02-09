import os
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from image.models import Image


class Command(BaseCommand):
    help = "更新图片名"

    def handle(self, *args, **options):
        images = Image.objects.all()
        for image in images:
            # self.stdout.write(self.style.SUCCESS("Hello, world!"))
            old_filename = image.image.name
            # print(old_filename)
            if 'new' not in image.image.name:
                old_path = os.path.join(settings.MEDIA_ROOT, old_filename)
                # print(old_path)

                created_date = image.item.created_at.strftime('%Y/%m/%d')

                ext = old_filename.split('.')[-1]
                filename = f"{image.id}_{uuid4().hex}"
                new_filename = f"uploads/new/{created_date}/{filename}.{ext}"
                new_path = os.path.join(settings.MEDIA_ROOT, new_filename)
                # print(new_path)

                new_directory = os.path.dirname(new_path)
                os.makedirs(new_directory, exist_ok=True)

                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    image.image.name = new_filename
                    image.filename = filename
                    image.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'图片重命名为：{new_filename}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'文件不存在：{old_path}')
                    )
            else:
                if image.filename is None:
                    image.filename = old_filename.split('/')[-1].split('.')[0]
                    image.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'图片添加filename字段值：{old_filename.split('/')[-1].split('.')[0]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'文件已经是新的，跳过：{old_filename}')
                    )

        # for poll_id in options["poll_ids"]:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)
        #
        #     poll.opened = False
        #     poll.save()
        #
        #     self.stdout.write(
        #         self.style.SUCCESS('Successfully closed poll "%s"' % poll_id)
        #     )