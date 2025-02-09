from django.db import models
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import Category, Software, SoftwareImage, Style, Item, Author, Model, Image
from .forms import ItemAdminForm, SoftwareAdminForm

from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminRadioSelectWidget, UnfoldAdminTextInputWidget

from django.template.loader import get_template


class SoftwareImageInline(TabularInline):
    model = SoftwareImage
    fields = ('image',)
    readonly_fields = ('image',)
    extra = 0
    max_num = 0


@admin.register(Software)
class SoftwareAdmin(ModelAdmin):
    form = SoftwareAdminForm
    inlines = [SoftwareImageInline]
    fields = ['name', 'thumbnail', 'model', 'url', 'description', ('pros', 'cons'), 'images']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.save_images(form.instance)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.enctype = "multipart/form-data"  # 确保编码类型正确

        return form


@admin.register(Style)
class StyleAdmin(ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ['name', 'user', 'user__profile__nickname']
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Model)
class AiModelAdmin(ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(SoftwareImage)
class SoftwareImageAdmin(ModelAdmin):
    list_display = ['software', 'software__name']


@admin.register(Image)
class ImageAdmin(ModelAdmin):
    list_display = ['item', 'filename', 'item__author']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            user_author = getattr(request.user, 'author', None)
            if user_author:
                return qs.filter(item__author=user_author)
            else:
                return qs.none()
        return qs


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'description', 'thumbnail', 'indented_name', 'parent', 'display_subcategories')

    def indented_name(self, obj):
        """在后台列表中为二级分类添加缩进"""
        if obj.parent:
            return f"{obj.parent.name} →|-- {obj.name}"
        return obj.name
    indented_name.short_description = "分类名称"
    indented_name.allow_tags = True  # 支持 HTML 显示

    def display_subcategories(self, obj):
        """显示所有二级分类"""
        subcategories = obj.subcategories.all()
        return ", ".join([sub.name for sub in subcategories])
    display_subcategories.short_description = "二级分类"

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser



class ShowImageInline(StackedInline):
    model = Image
    fields = ("show_thumbnail",)
    readonly_fields = ("show_thumbnail",)
    max_num = 0

    def show_thumbnail(self, instance):
        """A (pseudo)field that returns an image thumbnail for a show photo."""
        tpl = get_template("admin/show_thumbnail.html")
        return tpl.render({"image": instance.image})

    show_thumbnail.short_description = "缩略图" 


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    form = ItemAdminForm
    fields = [('prompt', 'cn_prompt'), 'author', 'tags', 'category', 'software', 'style', 'language', ('status', 'reviewed_by', 'reviewed_at'), 'images', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at', 'reviewed_by', 'reviewed_at')
    list_display = ('cn_prompt', 'author', 'category', 'software', 'style', 'status', 'created_at')
    inlines = [ShowImageInline]
    formfield_overrides = {
        # models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 30})}
        models.TextField: {'widget': UnfoldAdminTextareaWidget()},
        # 'taggit.managers.TaggableManager': {'widget', UnfoldAdminTextInputWidget()}
        # models.ForeignKey: {'widget': UnfoldAdminRadioSelectWidget()}
    }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'software' or db_field.name == 'style':  # 检查字段名
            kwargs['widget'] = UnfoldAdminRadioSelectWidget()

        if db_field.name == 'author':
            user_author = getattr(request.user, 'author', None)
            if user_author and request.user.is_superuser:
                kwargs['initial'] = user_author
            elif user_author:
                kwargs['queryset'] = Author.objects.filter(id=user_author.id)
                kwargs['initial'] = user_author
                # kwargs['widget'].attrs['readonly'] = True
            else:
                kwargs['queryset'] = Author.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # radio_fields = {
    #     "software": admin.HORIZONTAL,
    #     "style": admin.HORIZONTAL
    # }
    search_fields = ['prompt', 'cn_prompt']
    list_filter = ['author', 'category', 'software', 'style', 'status']
    actions = ['approve_items', 'reject_items']

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('status', 'reviewed_by')
        return super().get_readonly_fields(request, obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.save_images(form.instance)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.enctype = "multipart/form-data"  # 确保编码类型正确

        return form

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        user_author = getattr(request.user, 'author', None)
        if user_author and not request.user.is_superuser:
            return [field for field in fields if field != 'author']
        return fields
    
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user

        if not request.user.is_superuser and 'status' in form.changed_data:
            raise PermissionDenied("你没有权限更改状态！")
        if not request.user.is_superuser and 'reviewed_by' in form.changed_data:
            raise PermissionDenied("你没有权限更改审核人员！")
        if 'status' in form.changed_data and obj.status in ['approved', 'rejected']:
            obj.reviewed_by = request.user

        if not obj.author and hasattr(request.user, 'author') and request.user.author:
            obj.author = request.user.author
        
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author__user=request.user)

    @admin.action(description='审核通过所选内容')
    def approve_items(self, request, queryset):
        # queryset.update(status='approved')
        for item in queryset:
            item.status = 'approved'
            item.reviewed_by = request.user
            item.save()
        self.message_user(request, '所选内容已审核通过')

    @admin.action(description='拒绝所选内容')
    def reject_items(self, request, queryset):
        # queryset.update(status='rejected')
        for item in queryset:
            item.status = 'rejected'
            item.reviewed_by = request.user
            item.save()
        self.message_user(request, '所选内容已被拒绝')

