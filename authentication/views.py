from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from .forms import CreateUserForm, UpdateProfileForm

from image.models import Item, Software


def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser


@login_required
def homepage(request):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    today_items = Item.objects.filter(
        is_deleted=False,
        created_at__date=today,
        status="approved"
    ).order_by('-created_at').prefetch_related('images')

    yesterday_items = Item.objects.filter(
        is_deleted=False,
        created_at__date=yesterday,
        status="approved"
    ).order_by('-created_at').prefetch_related('images')

    day_before_yesterday_items = Item.objects.filter(
        is_deleted=False,
        created_at__date=day_before_yesterday,
        status="approved"
    ).order_by('-created_at').prefetch_related('images')

    latest_items = Item.objects.filter(
        is_deleted=False,
        status="approved"
    ).order_by('-created_at').prefetch_related('images')[:20]

    software = Software.objects.all().prefetch_related('images')

    data = [
        {
            'date': today,
            'label': '今日新增',
            'items': today_items,
        },
        {
            'date': yesterday,
            'label': '昨日新增',
            'items': yesterday_items,
        },
        {
            'date': day_before_yesterday,
            'label': '前天新增',
            'items': day_before_yesterday_items
        },
        {
            'date': None,
            'label': '最近上传',
            'items': latest_items,
        }
    ]

    return render(request, 'index.html', {
        'data': data,
        'software': software,
    })


def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "注册成功")
            return redirect(reverse('authentication:login'))
        else:
            messages.error(request, "注册失败")
    else:
        form = CreateUserForm()

    return render(request, 'authentication/register.html', {'form': form})


class LoginView(LoginView):
    template_name = 'authentication/login.html'


@login_required
def profile(request):
    if request.method == "POST":
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
    else:
        profile_form = UpdateProfileForm(instance=request.user.profile)
    return render(request, 'authentication/profile.html', {'profile_form': profile_form})


@login_required
@user_passes_test(is_staff_or_superuser, login_url='authentication:forbidden')
def my_upload(request):
    if request.user.is_superuser:
        data = Item.objects.filter(is_deleted=False).order_by('-created_at')
    else:
        data = Item.objects.filter(author__user=request.user, is_deleted=False).order_by('-created_at')

    if request.GET.get('status') and request.GET.get('status') != 'all':
        data = data.filter(status=request.GET.get('status'))

    paginator = Paginator(data, 10)
    page = request.GET.get('page', 1)
    data = paginator.get_page(page)

    return render(request, 'authentication/my-upload.html', {
        'data': data,
        'status': request.GET.get('status'),
        'all_count': Item.objects.filter(
            is_deleted=False).count() if request.user.is_superuser else Item.objects.filter(author__user=request.user,
                                                                                            is_deleted=False).count(),
        'approved_count': Item.objects.filter(status="approved",
                                              is_deleted=False).count() if request.user.is_superuser else Item.objects.filter(
            author__user=request.user, status="approved", is_deleted=False).count(),
        'rejected_count': Item.objects.filter(status="rejected",
                                              is_deleted=False).count() if request.user.is_superuser else Item.objects.filter(
            author__user=request.user, status="rejected", is_deleted=False).count(),
        'pending_count': Item.objects.filter(status="pending",
                                             is_deleted=False).count() if request.user.is_superuser else Item.objects.filter(
            author__user=request.user, status="pending", is_deleted=False).count()
    })


def forbidden(request):
    return render(request, 'authentication/forbidden.html')
