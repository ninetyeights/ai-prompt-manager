from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now, localtime
from zoneinfo import ZoneInfo

from .forms import ItemForm, ImageForm
from .models import Item, Category, Image, Author


def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser

def is_superuser(user):
    return user.is_superuser


@login_required
def update_copy_count(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(Item, pk=pk)
        user_key = f"user_copy_count{request.user.id}_{pk}"

        if not cache.get(user_key):
            item.copy_count += 1
            item.save()
            cache.set(user_key, True, 60 * 30)

        return JsonResponse({
            'copy_count': item.copy_count
        })

    return JsonResponse({
        'error': '只允许POST方法'
    })


@login_required
def update_view_count(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(Item, pk=pk)
        user_key = f"user_view_count{request.user.id}_{pk}"

        if not cache.get(user_key):
            item.views += 1
            item.save()
            cache.set(user_key, True, 60 * 30)

        return JsonResponse({
            'views': item.views
        })

    return JsonResponse({
        'error': '只允许POST方法'
    })


@login_required
def category(request, pk):
    data = Item.objects.filter(category__pk=pk, status="approved").order_by('-created_at')
    category = get_object_or_404(Category, pk=pk)

    return render(request, 'image/category.html', {
        'data': data,
        'category': category
    })


@login_required
@user_passes_test(is_staff_or_superuser, login_url='authentication:forbidden')
def delete_item(request, pk):
    if request.method == 'DELETE':
        item = get_object_or_404(Item, pk=pk)

        if item.author.user != request.user and not request.user.is_superuser:
            return JsonResponse({'error': '你没有权限删除这个条目'}, status=403)

        item.delete()
        return JsonResponse({'message': '条目已删除'}, status=200)
    return JsonResponse({'error': '请求方法无效'}, status=400)


@login_required
@user_passes_test(is_staff_or_superuser, login_url='authentication:forbidden')
def update_item(request, pk=None):
    instance = get_object_or_404(Item, pk=pk) if pk else None
    # print(instance)

    if request.method == 'POST':
        # print(request.POST)
        # print(request.FILES)

        form = ItemForm(request.POST, instance=instance, user=request.user)

        images = request.FILES.getlist('image')
        existing_images = request.POST.getlist('existing_image_names', [])

        # print(images)
        # print(existing_images)

        if form.is_valid() and images:
            instance = form.save()

            db_images = instance.images.all()

            for db_image in db_images:
                if db_image.filename not in existing_images:
                    db_image.delete()

            for image in images:
                filename = image.name.split('.')[0]
                if filename in existing_images:
                    continue

                image_instance = Image(item=instance, image=image)
                image_instance.save()

            # context = {
            #     'item': instance,
            #     'form': form,
            #     'pk': pk,
            #     'existing_images': [{
            #         'id': image.id,
            #         'filename': image.filename,
            #         'size': image.image.size,
            #         'url': request.build_absolute_uri(image.image.url)
            #     }
            #         for image in instance.images.all()] if instance else []
            # }

            # return render(request, 'image/update_item.html', context)
            # item = form.save(commit=False)
            # item.save()
            # form.save_m2m()
            #
            # for image in images:
            #     Image.objects.create(item=item, image=image)
            #
            return redirect('authentication:my_upload')

            # existing_images = [{'id': image.id, 'url': request.build_absolute_uri(image.image.url)} for image in Image.objects.filter(item=item)]
        else:
            return render(request, 'image/update_item.html', {
                'form': form,
                'errors': form.errors,
                'pk': pk,
                'existing_images': []
            })
    else:
        form = ItemForm(instance=instance, user=request.user)

        existing_images = [{
            'id': image.id,
            'filename': image.filename,
            'size': image.image.size,
            'url': request.build_absolute_uri(image.image.url)
        }
            for image in instance.images.all()] if instance else []

        context = {
            'item': instance,
            'form': form,
            'pk': pk,
            'existing_images': existing_images
        }

    return render(request, 'image/update_item.html', context)

@login_required
@user_passes_test(is_superuser, login_url='authentication:forbidden')
def approve_item(request, pk):
    if request.method == 'GET':
        item = get_object_or_404(Item, pk=pk)
        if request.user.is_superuser:
            item.status = 'approved'
            item.reviewed_by = request.user
            item.reviewed_at = localtime(now().astimezone(ZoneInfo('America/Sao_Paulo')))
            item.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

    url = reverse('authentication:my_upload')
    redirect_url = f"{url}?status={request.GET.get('status')}"
    return redirect(redirect_url)


@login_required
@user_passes_test(is_superuser, login_url='authentication:forbidden')
def reject_item(request, pk):
    if request.method == 'GET':
        item = get_object_or_404(Item, pk=pk)
        if request.user.is_superuser:
            item.status = 'rejected'
            item.rejection_reason = request.GET.get('reason')
            item.reviewed_by = request.user
            item.reviewed_at = localtime(now().astimezone(ZoneInfo('America/Sao_Paulo')))
            item.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

    url = reverse('authentication:my_upload')
    redirect_url = f"{url}?status={request.GET.get('status')}"
    return redirect(redirect_url)
