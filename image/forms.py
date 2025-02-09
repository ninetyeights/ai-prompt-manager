from django import forms
from django.core.validators import validate_image_file_extension
from django.utils.timezone import localtime, now
from zoneinfo import ZoneInfo
from django.utils.translation import gettext as _
from django.forms.models import inlineformset_factory
from django.forms.widgets import FileInput
from django.contrib.auth.models import User
from taggit.forms import TagField, TagWidget

from .models import Item, Image, Category, Author, Software, SoftwareImage

from unfold.widgets import UnfoldAdminFileFieldWidget


class MultiFileInput(UnfoldAdminFileFieldWidget):
    allow_multiple_selected = True  # 允许选择多个文件


class MultiFileField(forms.FileField):
    def __init__(self, *args, allowed_extensions=None, **kwargs):
        # 设置默认的 widget 为自定义的 MultiFileInput
        kwargs['widget'] = MultiFileInput()
        super().__init__(*args, **kwargs)
        self.allowed_extensions = allowed_extensions

    def clean(self, data, initial=None):
        # 检查是否提交了多个文件
        if not data:
            return []
        if not isinstance(data, list):
            data = [data]
        for file in data:
            self.validate(file)
            self.run_validators(file)
            if self.allowed_extensions and not file.name.split('.')[-1].lower() in self.allowed_extensions:
                raise forms.ValidationError(
                    _("File extension not allowed. Allowed extensions are: %(extensions)s."),
                    params={"extensions": ", ".join(self.allowed_extensions)},
                )
        return data


class SoftwareAdminForm(forms.ModelForm):
    class Meta:
        model = Software
        fields = "__all__"

    images = MultiFileField(
        label=_("添加图片"),
        required=False,
    )

    def clean_images(self):
        """Make sure only images can be uploaded."""
        uploads = self.files.getlist("images")
        for upload in uploads:
            validate_image_file_extension(upload)
        return uploads

    def save_images(self, item):
        """Process each uploaded image."""
        print(item)
        print(self.files.getlist("images"))
        for upload in self.files.getlist("images"):
            photo = SoftwareImage(software=item, image=upload)
            photo.save()


class ItemAdminForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = "__all__"

    images = MultiFileField(
        label=_("添加图片"),
        required=False,
    )

    def clean_images(self):
        """Make sure only images can be uploaded."""
        uploads = self.files.getlist("images")
        for upload in uploads:
            validate_image_file_extension(upload)
        return uploads

    def save_images(self, item):
        """Process each uploaded image."""
        for upload in self.files.getlist("images"):
            photo = Image(item=item, image=upload)
            photo.save()


def get_category_choices(categories, level=0):
    """
    递归生成分类选项，使用缩进区分层级
    """
    choices = []
    for category in categories:
        choices.append((category.id, category.name, level))
        # 递归处理子分类
        children = category.subcategories.all()
        if children.exists():  # 如果子分类存在，则递归添加
            choices.extend(get_category_choices(children, level + 1))
    return choices


class ItemForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[],  # choices 会在 __init__ 中动态加载
        label="分类",  # 字段的显示标签
        widget=forms.RadioSelect,  # 使用单选按钮小部件
    )

    # tags = TagField(widget=forms.TextInput(attrs={'placeholder': '输入标签',
    #                                        'class': 'w-full bg-white placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow'}))

    tags = TagField(
        required=False,
        widget=TagWidget(attrs={
            'placeholder': '输入标签',
            'class': 'w-full bg-white placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow'
        })
    )

    class Meta:
        model = Item
        fields = [
            'prompt',
            'cn_prompt',
            'category',
            'software',
            'style',
            'language',
            'tags',
            'author',
            'status',
            'rejection_reason'
            # 'reviewed_by'
        ]
        # 添加自定义小部件或属性
        widgets = {
            'prompt': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2 resize-none',
                'placeholder': '输入提示词'}),
            'cn_prompt': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2 resize-none',
                'placeholder': '输入中文提示词'}),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-2 resize-none',
                'placeholder': '输入中文提示词'}),
            'software': forms.RadioSelect,
            'style': forms.RadioSelect,
            'language': forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        if not self.user.is_superuser:
            for field in ['author', 'status']:
                if field in self.fields:
                    del self.fields[field]

        # 获取顶级分类
        root_categories = Category.objects.filter(parent__isnull=True)
        # 递归生成 choices
        category_choices = get_category_choices(root_categories)
        # 动态分配到 category 字段
        self.fields['category'].choices = [(item[0], item[1]) for item in category_choices]
        self.category_choices = category_choices

        if self.instance.pk:
            self.fields['tags'].initial = ', '.join(tag.name for tag in self.instance.tags.all())

        STATUS_CHOICES = [
            ('pending', '待审核'),
            ('approved', '审核通过'),
            ('rejected', '已拒绝')
        ]

        # self.initial['category'] = self.instance.category.id if self.instance.category else None

        if self.user.is_superuser:
            self.fields['author'] = forms.ModelChoiceField(
                queryset=Author.objects.all(),
                required=True,
                label="生成人员",
                widget=forms.Select(attrs={
                    'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded pl-3 pr-8 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-400 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
                })
            )

            if not self.initial.get('author'):
                try:
                    self.initial['author'] = Author.objects.get(user=self.user)
                except Author.DoesNotExist:
                    self.initial['author'] = None

            # `status` 可修改
            self.fields['status'] = forms.ChoiceField(
                choices=STATUS_CHOICES,
                label="审核状态",
                widget=forms.Select(attrs={
                    'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white'
                })
            )

            if not self.initial.get('status'):
                self.initial['status'] = 'pending'

            # `reviewed_by` 字段设置为只读（禁止手动修改）
            # self.fields['reviewed_by'] = forms.ModelChoiceField(
            #     queryset=User.objects.filter(pk=self.user.id),
            #     required=False,
            #     widget=forms.Select(attrs={
            #         'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
            #         'readonly': 'readonly'
            #     })
            # )
        # else:
        #     try:
        #         author = Author.objects.get(user=self.user)
        #         self.fields['author'] = forms.ModelChoiceField(
        #             queryset=Author.objects.filter(user=author.user),
        #             required=True,
        #             label="生成人员",
        #             widget=forms.Select(attrs={
        #                 'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded pl-3 pr-8 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-400 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
        #                 'readonly': 'readonly'
        #             })
        #         )
        #         self.initial['author'] = author
        #     except Author.DoesNotExist:
        #         self.fields['author'] = forms.ModelChoiceField(
        #             queryset=Author.objects.all(),
        #             required=True,
        #             label="生成人员",
        #             widget=forms.Select(attrs={
        #                 'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded pl-3 pr-8 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-400 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
        #             })
        #         )
        #         self.initial['author'] = None
        #
        #     # 非超级用户逻辑：禁用 `status` 和 `reviewed_by`
        #     self.fields['status'] = forms.ChoiceField(
        #         choices=STATUS_CHOICES,
        #         label="审核状态",
        #         widget=forms.Select(attrs={
        #             'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
        #             'readonly': 'readonly'
        #         })
        #     )
        #     self.fields['reviewed_by'] = forms.ModelChoiceField(
        #         queryset=User.objects.all(),
        #         required=False,
        #         label="审核人员",
        #         widget=forms.Select(attrs={
        #             'class': 'w-full placeholder:text-slate-400 text-slate-700 text-sm border border-slate-200 rounded-md px-3 py-2 transition duration-300 ease focus:outline-none focus:border-slate-400 hover:border-slate-300 shadow-sm focus:shadow-md appearance-none cursor-pointer bg-white',
        #             'readonly': 'readonly'
        #         })
        #     )
        #
        # self.initial['status'] = self.instance.status
        # self.initial['reviewed_by'] = self.instance.reviewed_by
        #
        # if 'author' in self.fields:
        #     self.fields['author'].widget.attrs['data-initial'] = self.initial['author']
        #
        # if 'reviewed_by' in self.fields:
        #     self.fields['reviewed_by'].widget.attrs['data-initial'] = self.initial['reviewed_by']

        # 确保 category 使用 RadioSelect
        # self.fields['category'].widget = forms.RadioSelect

    # def clean_tags(self):
    #     tags = self.cleaned_data.get('tags', [])
    #     tag_names = [tag.strip() for tag in tags if tag.strip()]
    #     print(tag_names)
    #     return tag_names

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.uploaded_by = self.user

        if not self.user.is_superuser:
            try:
                instance.author = Author.objects.get(user=self.user)
            except Author.DoesNotExist:
                instance.author = None

            if instance.id:
                instance.status = instance._meta.model.objects.get(
                    pk=instance.id).status if instance._meta.model.objects.get(pk=instance.id) else 'pending'
                instance.reviewed_by = instance._meta.model.objects.get(
                    pk=instance.id).reviewed_by if instance._meta.model.objects.get(pk=instance.id) else None
                instance.rejection_reason = instance._meta.model.objects.get(pk=instance.id).rejection_reason
            else:
                instance.status = 'pending'
                instance.reviewed_by = None
                instance.rejection_reason = None

        if self.user.is_superuser:
            instance.status = self.cleaned_data['status']
            instance.reviewed_by = self.user
            instance.reviewed_at = localtime(now().astimezone(ZoneInfo('America/Sao_Paulo')))

            if 'status' in self.changed_data:
                instance.reviewed_by = self.user


        if commit:
            instance.save()

            # tag_names = self.cleaned_data.get('tags', [])
            # print(tag_names)
            # if tag_names:
            #     tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
            #     instance.tags.set(tag_objects)
            # else:
            #     instance.tags.clear()

            self.save_m2m()

        return instance

    def clean_category(self):
        # 获取用户提交的值
        category_id = self.cleaned_data.get('category')
        try:
            # 将主键值转换为 Category 实例
            category_instance = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise forms.ValidationError("所选分类不存在")
        return category_instance  # 返回实例，而非 ID


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']
        widgets = {
            'image': MultiFileInput,
        }

    def clean_image(self):
        print(11111111)
        uploaded_images = self.cleaned_data.get('image')
        print(uploaded_images)

        if not uploaded_images:
            raise forms.ValidationError("请提供一张图片。")


# Inline Formset 关联 `Item` 和 `Image` 模型
ImageFormSet = inlineformset_factory(
    Item,
    Image,
    form=ImageForm,
    extra=1,  # 默认多出一个空表单用于添加新图片
    can_delete=True,  # 允许删除图片
)


class MultiFileInput(FileInput):
    """
    自定义多文件上传小部件
    """

    def __init__(self, attrs=None):
        # 在 attributes 中添加 multiple 属性
        attrs = attrs or {}
        attrs.update({'multiple': 'multiple'})
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        # 返回多个文件的处理
        return files.getlist(name)
