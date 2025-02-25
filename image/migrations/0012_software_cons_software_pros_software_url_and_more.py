# Generated by Django 5.1.4 on 2025-01-27 17:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0011_item_reviewed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='software',
            name='cons',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='缺点'),
        ),
        migrations.AddField(
            model_name='software',
            name='pros',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='优点'),
        ),
        migrations.AddField(
            model_name='software',
            name='url',
            field=models.URLField(blank=True, null=True, verbose_name='软件链接'),
        ),
        migrations.CreateModel(
            name='SoftwareImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='software_images/')),
                ('software', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='image.software')),
            ],
        ),
    ]
