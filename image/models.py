from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from taggit.managers import TaggableManager
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

from datetime import datetime
from uuid import uuid4


class Category(models.Model):
    name = models.CharField(max_length=128, verbose_name="名称", unique=True)
    description = models.CharField(max_length=512, blank=True, null=True, verbose_name="描述")
    thumbnail = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name="缩略图")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="subcategories", on_delete=models.CASCADE, verbose_name="父级"
    )

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "分类"
        verbose_name_plural = verbose_name

    @property
    def item_count(self):
        return self.items.filter(status='approved').count()



class Model(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="名称")  # AI 模型名称
    description = models.TextField(blank=True, null=True, verbose_name="描述")  # 描述
    version = models.CharField(max_length=50, blank=True, null=True, verbose_name="版本")  # 版本号

    def __str__(self):
        return self.name
    

    class Meta:
        verbose_name = "模型"
        verbose_name_plural = verbose_name


class Software(models.Model):
    name = models.CharField(max_length=128, verbose_name="名称", unique=True)
    description = models.CharField(max_length=512, blank=True, null=True, verbose_name="描述")
    thumbnail = models.ImageField(upload_to='software_images/', blank=True, null=True, verbose_name="缩略图")
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="software", null=True, blank=True)
    pros = models.CharField(max_length=256, blank=True, null=True, verbose_name="优点")
    cons = models.CharField(max_length=256, blank=True, null=True, verbose_name="缺点")
    url = models.URLField(blank=True, null=True, verbose_name="软件链接")

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "软件"
        verbose_name_plural = verbose_name


class SoftwareImage(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='software_images/')
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFit(250, 250)],
        format='JPEG',
        options={'quality': 60}
    )


class Style(models.Model):
    name = models.CharField(max_length=128, verbose_name="名称", unique=True)
    description = models.CharField(max_length=512, blank=True, null=True, verbose_name="描述")
    thumbnail = models.ImageField(upload_to='style_images/', blank=True, null=True, verbose_name="缩略图")

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "风格"
        verbose_name_plural = verbose_name


class Author(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="生成人员")
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="author",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
    

    class Meta:
        verbose_name = "生成人员"
        verbose_name_plural = verbose_name


class Item(models.Model):
    prompt = models.TextField(verbose_name="提示词")
    cn_prompt = models.TextField(verbose_name="中文提示词")
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items',
        verbose_name="生成人员"
    )
    # images = models.JSONField(default=list, verbose_name="图片", blank=True)
    tags = TaggableManager(blank=True)

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items", verbose_name="分类")
    software = models.ForeignKey(Software, on_delete=models.SET_NULL, null=True, related_name="items", verbose_name="软件")
    style = models.ForeignKey(Style, on_delete=models.SET_NULL, null=True, related_name="items", verbose_name="风格")

    LANGUAGE_CHOICES = {
        "BR": "巴西葡语",
        "ES": "西语",
        "MJ": "美加",
    }

    language = models.CharField(max_length=32, choices=LANGUAGE_CHOICES, default="BR", verbose_name="语系")

    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    copy_count = models.PositiveIntegerField(default=0)

    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '已拒绝')
    ]
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending', verbose_name="审核状态")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_items',
        verbose_name='审核人员'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="审核日期"
    )

    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="拒绝原因"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_items',
        null=True,
        blank=True
    )

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def __str__(self):
        return self.cn_prompt

    
    class Meta:
        verbose_name = "条目"
        verbose_name_plural = verbose_name

class Image(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to='uploads/%Y/%m/%d')
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFit(250, 250)],
        format='JPEG',
        options={'quality': 60}
    )
    thumbnail_large = ImageSpecField(
        source='image',
        processors=[ResizeToFit(800, 800)],
        format='JPEG',
        options={'quality': 80}
    )
    filename = models.CharField(max_length=256, blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            ext = self.image.name.split('.')[-1]
            new_filename = f"{self.pk}_{uuid4().hex}"
            # new_path = f"uploads/{self.image.field.upload_to}/{new_filename}"

            today = datetime.today()
            date_path = today.strftime("%Y/%m/%d")
            new_path = f"uploads/new/{date_path}/{new_filename}.{ext}"

            self.image.storage.save(new_path, self.image)
            self.image.name = new_path
            self.filename = new_filename
            super().save(update_fields=['image', 'filename'])

    def __str__(self):
        return self.item.cn_prompt

    class Meta:
        verbose_name = "图片"
        verbose_name_plural = verbose_name
